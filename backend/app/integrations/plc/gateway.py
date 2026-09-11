from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.production_order import ProductionOrder
from app.models.production_unit import ProductionUnit
from app.schemas.pallet import PalletizeRequest, PalletizeResult
from app.services.pallet_service import PalletService

PlcSource = Literal["SIMULATOR", "PHYSICAL"]
SimulatorCommunicationState = Literal["ONLINE", "DISCONNECTED"]
SimulatorControlAction = Literal["DISCONNECT", "RECONNECT", "TIMEOUT_NEXT", "TIMEOUT_RETRY_CYCLE", "RESET"]


@dataclass(frozen=True)
class PlcConfirmation:
    line_id: int
    production_unit_id: int
    source: PlcSource = "SIMULATOR"
    signal: str = "PALLETIZE_CONFIRMED"
    rejection_reason: str | None = None


@dataclass(frozen=True)
class PlcGatewayOutcome:
    accepted: bool
    confirmation_status: str
    message: str
    error_code: str | None = None
    result: PalletizeResult | None = None
    retry_attempts: int = 1
    retry_max_attempts: int = 1
    retry_exhausted: bool = False
    last_retry_error: str | None = None


class PlcGateway:
    """Fronteira da integração com CLP/robô.

    ETAPA 7.10 mantém o estado seguro da 7.9 e acrescenta retentativa
    controlada para timeout. Sem ACK aceito, nenhuma unidade é paletizada.
    O contrato continua independente do hardware real.
    """

    simulator_adapter = "SIMULATOR_PLC_V1"

    def __init__(self) -> None:
        self.pallet_service = PalletService()
        self._communication_state: SimulatorCommunicationState = "ONLINE"
        self._timeouts_remaining = 0
        self._last_transition_at = self._now_iso()
        self._last_retry_attempts = 0
        self._last_retry_error: str | None = None
        self._last_retry_exhausted = False

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def communication_status(self) -> dict:
        ready = self._communication_state == "ONLINE"
        return {
            "communication_state": self._communication_state,
            "ready": ready,
            "safe_state": not ready or self._timeouts_remaining > 0,
            "timeout_next": self._timeouts_remaining > 0,
            "timeouts_remaining": self._timeouts_remaining,
            "timeout_seconds": max(1, int(settings.plc_simulator_timeout_seconds)),
            "retry_max_attempts": max(1, int(settings.plc_retry_max_attempts)),
            "retry_interval_seconds": max(0, int(settings.plc_retry_interval_seconds)),
            "last_retry_attempts": self._last_retry_attempts,
            "last_retry_error": self._last_retry_error,
            "last_retry_exhausted": self._last_retry_exhausted,
            "last_transition_at": self._last_transition_at,
        }

    def status(self) -> dict:
        communication = self.communication_status()
        return {
            "mode": "SIMULATOR",
            "ready": communication["ready"],
            "hardware_connected": False,
            "active_adapter": self.simulator_adapter,
            "supported_sources": ["SIMULATOR"],
            "supported_signals": ["PALLETIZE_CONFIRMED", "PALLETIZE_REJECTED"],
            "communication_state": communication["communication_state"],
            "safe_state": communication["safe_state"],
            "timeout_next": communication["timeout_next"],
            "timeout_seconds": communication["timeout_seconds"],
            "timeouts_remaining": communication["timeouts_remaining"],
            "retry_max_attempts": communication["retry_max_attempts"],
            "retry_interval_seconds": communication["retry_interval_seconds"],
            "last_retry_attempts": communication["last_retry_attempts"],
            "last_retry_error": communication["last_retry_error"],
            "last_retry_exhausted": communication["last_retry_exhausted"],
            "last_transition_at": communication["last_transition_at"],
            "message": (
                "Contrato do CLP pronto em modo simulado com sincronização persistida, "
                "ACK/NACK, timeout, desconexão/reconexão, estado seguro e retentativa controlada. Hardware físico ainda não conectado."
            ),
        }

    def control_simulator(self, action: SimulatorControlAction) -> dict:
        if action == "DISCONNECT":
            self._communication_state = "DISCONNECTED"
            self._timeouts_remaining = 0
        elif action == "RECONNECT":
            self._communication_state = "ONLINE"
            self._timeouts_remaining = 0
        elif action == "TIMEOUT_NEXT":
            if self._communication_state != "ONLINE":
                raise HTTPException(status_code=409, detail="Reconecte o simulador antes de programar um timeout.")
            self._timeouts_remaining = 1
        elif action == "TIMEOUT_RETRY_CYCLE":
            if self._communication_state != "ONLINE":
                raise HTTPException(status_code=409, detail="Reconecte o simulador antes de programar falhas de retentativa.")
            self._timeouts_remaining = max(1, int(settings.plc_retry_max_attempts))
        elif action == "RESET":
            self._communication_state = "ONLINE"
            self._timeouts_remaining = 0
            self._last_retry_attempts = 0
            self._last_retry_error = None
            self._last_retry_exhausted = False
        else:
            raise HTTPException(status_code=422, detail="Ação de simulador não suportada")
        self._last_transition_at = self._now_iso()
        return self.status()

    def inspect_cycle(self, db: Session, line_id: int, production_unit_id: int) -> dict:
        repository = self.pallet_service.repository
        unit = repository.get_unit(db, production_unit_id)
        if not unit:
            raise HTTPException(status_code=404, detail="Unidade não encontrada")

        order = db.get(ProductionOrder, unit.production_order_id)
        if not order:
            raise HTTPException(status_code=404, detail="OP da unidade não encontrada")

        base = {
            "line_id": line_id,
            "production_unit_id": unit.id,
            "production_order_id": unit.production_order_id,
            "serial_number": unit.serial_number,
            "unit_status": unit.status,
        }

        if order.line_id != line_id:
            return {
                **base,
                "synchronized": False,
                "state": "CONTEXT_MISMATCH",
                "can_confirm": False,
                "can_reject": False,
                "message": f"A unidade pertence à linha {order.line_id}; o contexto informado é a linha {line_id}.",
                "next_action": "SELECIONAR_LINHA_CORRETA",
                "pallet": None,
            }

        item = repository.get_pallet_item_by_unit(db, unit.id)
        if item:
            pallet = repository.get_pallet(db, item.pallet_id)
            completed = bool(pallet and pallet.status == "FULL")
            return {
                **base,
                "synchronized": True,
                "state": "PALLETIZED",
                "can_confirm": False,
                "can_reject": False,
                "message": "Unidade já confirmada pelo ciclo de paletização e sincronizada com o MySQL.",
                "next_action": "INICIAR_NOVO_PALETE" if completed else "AGUARDAR_PROXIMA_UNIDADE",
                "pallet": pallet,
            }

        if unit.status == "SCANNED":
            return {
                **base,
                "synchronized": True,
                "state": "AWAITING_PLC",
                "can_confirm": True,
                "can_reject": True,
                "message": "Leitura válida registrada; unidade aguardando retorno do CLP.",
                "next_action": "AGUARDAR_RETORNO_CLP",
                "pallet": None,
            }

        if unit.status == "PLC_REJECTED":
            return {
                **base,
                "synchronized": True,
                "state": "PLC_REJECTED",
                "can_confirm": False,
                "can_reject": False,
                "message": "Unidade rejeitada pelo CLP; nenhuma paletização foi gravada e o ciclo está liberado.",
                "next_action": "AGUARDAR_PROXIMA_UNIDADE",
                "pallet": None,
            }

        return {
            **base,
            "synchronized": False,
            "state": "BLOCKED_UNIT_STATE",
            "can_confirm": False,
            "can_reject": False,
            "message": f"Estado da unidade não permite confirmação do CLP: {unit.status}.",
            "next_action": "REVISAR_ESTADO_UNIDADE",
            "pallet": None,
        }

    def latest_cycle(self, db: Session, line_id: int, production_order_id: int) -> dict | None:
        order = db.get(ProductionOrder, production_order_id)
        if not order:
            raise HTTPException(status_code=404, detail="OP não encontrada")
        if order.line_id != line_id:
            raise HTTPException(status_code=409, detail="A OP selecionada não pertence à linha informada")

        unit = db.scalar(
            select(ProductionUnit)
            .where(ProductionUnit.production_order_id == production_order_id)
            .order_by(ProductionUnit.id.desc())
            .limit(1)
        )
        if not unit:
            return None

        return self.inspect_cycle(db, line_id, unit.id)

    def _communication_guard(self, confirmation: PlcConfirmation) -> PlcGatewayOutcome | None:
        if confirmation.source != "SIMULATOR":
            return None
        if self._communication_state != "ONLINE":
            return PlcGatewayOutcome(
                accepted=False,
                confirmation_status="COMMUNICATION_UNAVAILABLE",
                error_code="PLC_DISCONNECTED",
                message="Comunicação com o CLP simulada indisponível. Unidade mantida em estado seguro aguardando reconexão.",
            )
        if self._timeouts_remaining > 0:
            self._timeouts_remaining -= 1
            self._last_transition_at = self._now_iso()
            return PlcGatewayOutcome(
                accepted=False,
                confirmation_status="TIMEOUT",
                error_code="PLC_TIMEOUT",
                message=(
                    f"Timeout simulado de comunicação ({max(1, int(settings.plc_simulator_timeout_seconds))} s). "
                    "Nenhuma paletização foi gravada; tente novamente após confirmar a comunicação."
                ),
            )
        return None

    def process(self, db: Session, confirmation: PlcConfirmation) -> PlcGatewayOutcome:
        if confirmation.source == "PHYSICAL":
            raise HTTPException(status_code=409, detail="CLP físico ainda não configurado. Use o simulador até o equipamento e protocolo reais serem definidos.")
        if confirmation.source != "SIMULATOR":
            raise HTTPException(status_code=422, detail="Origem de CLP não suportada")
        if confirmation.signal not in {"PALLETIZE_CONFIRMED", "PALLETIZE_REJECTED"}:
            raise HTTPException(status_code=422, detail="Sinal de CLP não suportado")

        communication_failure = self._communication_guard(confirmation)
        if communication_failure is not None:
            return communication_failure

        sync = self.inspect_cycle(db, confirmation.line_id, confirmation.production_unit_id)

        if sync["state"] == "PALLETIZED":
            if confirmation.signal == "PALLETIZE_CONFIRMED":
                return PlcGatewayOutcome(
                    accepted=False,
                    confirmation_status="DUPLICATE_BLOCKED",
                    error_code="PLC_DUPLICATE_CONFIRMATION",
                    message="Confirmação duplicada bloqueada: esta unidade já foi paletizada.",
                )
            return PlcGatewayOutcome(
                accepted=False,
                confirmation_status="OUT_OF_SEQUENCE",
                error_code="PLC_SEQUENCE_INVALID",
                message="NACK fora de sequência: a unidade já foi confirmada e paletizada.",
            )

        if sync["state"] != "AWAITING_PLC":
            return PlcGatewayOutcome(
                accepted=False,
                confirmation_status="OUT_OF_SEQUENCE",
                error_code="PLC_SEQUENCE_INVALID",
                message=sync["message"],
            )

        if confirmation.signal == "PALLETIZE_REJECTED":
            # ETAPA 7.12 — NACK é uma decisão final para esta unidade, não uma
            # falha de comunicação. A unidade precisa sair de SCANNED para liberar
            # o fluxo da próxima leitura, sem jamais entrar em um palete.
            reason = (confirmation.rejection_reason or "Sinal rejeitado pelo CLP simulado").strip()
            unit = self.pallet_service.repository.get_unit(db, confirmation.production_unit_id)
            if not unit:
                raise HTTPException(status_code=404, detail="Unidade não encontrada")
            unit.status = "PLC_REJECTED"
            db.add(unit)
            db.commit()
            db.refresh(unit)
            return PlcGatewayOutcome(
                accepted=False,
                confirmation_status="REJECTED_BY_PLC",
                error_code="PLC_NACK",
                message=f"{reason}. Unidade rejeitada pelo CLP e ciclo liberado para a próxima leitura.",
            )

        try:
            result = self.pallet_service.palletize(
                db,
                PalletizeRequest(line_id=confirmation.line_id, production_unit_id=confirmation.production_unit_id),
            )
            return PlcGatewayOutcome(
                accepted=True,
                confirmation_status="CONFIRMED",
                message="Confirmação do CLP processada com sucesso.",
                result=result,
            )
        except HTTPException as exc:
            if exc.status_code == 409 and "já foi paletizada" in str(exc.detail):
                return PlcGatewayOutcome(
                    accepted=False,
                    confirmation_status="DUPLICATE_BLOCKED",
                    error_code="PLC_DUPLICATE_CONFIRMATION",
                    message="Confirmação duplicada bloqueada: esta unidade já foi paletizada.",
                )
            raise

    def process_with_retry(self, db: Session, confirmation: PlcConfirmation) -> PlcGatewayOutcome:
        """Processa o retorno com retentativa controlada somente para TIMEOUT.

        Desconexão exige reconexão explícita; NACK e erros de sequência não são
        repetidos automaticamente. Enquanto não existir ACK aceito, a unidade
        permanece SCANNED no MySQL e nenhuma associação com palete é criada.
        """
        max_attempts = max(1, int(settings.plc_retry_max_attempts))
        interval_seconds = max(0, int(settings.plc_retry_interval_seconds))
        self._last_retry_attempts = 0
        self._last_retry_error = None
        self._last_retry_exhausted = False

        last: PlcGatewayOutcome | None = None
        for attempt in range(1, max_attempts + 1):
            self._last_retry_attempts = attempt
            outcome = self.process(db, confirmation)
            last = outcome
            if outcome.confirmation_status != "TIMEOUT":
                # NACK é uma decisão funcional final e não participa do ciclo de
                # retentativa. ACK após timeout, porém, preserva o número real de
                # tentativas consumidas (ex.: sucesso em 2/3).
                nack_final = outcome.confirmation_status == "REJECTED_BY_PLC"
                return PlcGatewayOutcome(
                    accepted=outcome.accepted,
                    confirmation_status=outcome.confirmation_status,
                    message=(
                        f"{outcome.message} Retentativa controlada: {attempt}/{max_attempts} tentativa(s)."
                        if attempt > 1 else outcome.message
                    ),
                    error_code=outcome.error_code,
                    result=outcome.result,
                    retry_attempts=1 if nack_final else attempt,
                    retry_max_attempts=1 if nack_final else max_attempts,
                    retry_exhausted=False,
                    last_retry_error=self._last_retry_error,
                )

            self._last_retry_error = outcome.error_code or "PLC_TIMEOUT"
            if attempt < max_attempts and interval_seconds > 0:
                time.sleep(interval_seconds)

        self._last_retry_exhausted = True
        self._last_transition_at = self._now_iso()
        return PlcGatewayOutcome(
            accepted=False,
            confirmation_status="RETRIES_EXHAUSTED",
            error_code="PLC_RETRY_EXHAUSTED",
            message=(
                f"Retentativas esgotadas: {max_attempts}/{max_attempts} tentativas sem confirmação do CLP. "
                "Nenhuma paletização foi gravada; a unidade permanece aguardando intervenção/reconexão."
            ),
            result=None,
            retry_attempts=max_attempts,
            retry_max_attempts=max_attempts,
            retry_exhausted=True,
            last_retry_error=self._last_retry_error,
        )

    def confirm(self, db: Session, confirmation: PlcConfirmation) -> PalletizeResult:
        outcome = self.process(db, confirmation)
        if not outcome.accepted or outcome.result is None:
            raise HTTPException(status_code=409, detail=outcome.message)
        return outcome.result


def plc_cycle_state(result: PalletizeResult) -> tuple[str, bool, bool, str]:
    completed = bool(result.completed_now)
    new_pallet_started = bool(result.sequence_number == 1 and not completed)
    if completed:
        return "PALLET_COMPLETED", True, False, "INICIAR_NOVO_PALETE"
    if new_pallet_started:
        return "NEW_PALLET_STARTED", False, True, "AGUARDAR_PROXIMA_UNIDADE"
    return "PALLET_IN_PROGRESS", False, False, "AGUARDAR_PROXIMA_UNIDADE"
