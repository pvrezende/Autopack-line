from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import Enum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.plc_transaction import PlcTransaction


ACTIVE_TRANSACTION_STATUSES = {
    "PERSISTED_PENDING",
    "WAITING_ACK",
    "REQUEST_ACCEPTED",
    "WAITING_CYCLE_COMPLETION",
    "COMMUNICATION_LOST",
    "RECONCILE_REQUIRED",
}


class ReconciliationOutcome(str, Enum):
    ALREADY_COMPLETED_DEPOSITED = "ALREADY_COMPLETED_DEPOSITED"
    ALREADY_COMPLETED_REJECTED = "ALREADY_COMPLETED_REJECTED"
    ALREADY_COMPLETED_ABORTED = "ALREADY_COMPLETED_ABORTED"
    PLC_STILL_PROCESSING = "PLC_STILL_PROCESSING"
    ACK_KNOWN_WAIT_COMPLETION = "ACK_KNOWN_WAIT_COMPLETION"
    RESEND_SAME_SEQUENCE = "RESEND_SAME_SEQUENCE"
    CONFLICT_INTERVENTION = "CONFLICT_INTERVENTION"


@dataclass(frozen=True)
class PersistedRequest:
    request_sequence: int
    payload_hash: str
    status: str = "RECONCILE_REQUIRED"


@dataclass(frozen=True)
class PlcReconciliationSnapshot:
    ack_sequence: int
    machine_busy: bool
    completed_sequence: int
    completion_result: int
    result_code: int = 0
    pallet_sequence: int = 0
    boxes_on_pallet: int = 0


@dataclass(frozen=True)
class ReconciliationDecision:
    outcome: ReconciliationOutcome
    may_write: bool
    may_create_new_sequence: bool
    may_mark_palletized: bool
    same_request_sequence_required: bool
    requires_operator: bool
    next_action: str
    reason: str


def canonical_payload_hash(payload: dict) -> str:
    canonical = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def validate_request_sequence(value: int) -> int:
    if not 1 <= int(value) <= 0xFFFF:
        raise ValueError("REQUEST_SEQUENCE deve estar entre 1 e 65535.")
    return int(value)


def reconcile(persisted: PersistedRequest, plc: PlcReconciliationSnapshot) -> ReconciliationDecision:
    seq = validate_request_sequence(persisted.request_sequence)

    # D760/D761 are authoritative for physical completion.  This check must be
    # done before ACK/BUSY so a restart never repeats a unit already deposited.
    if plc.completed_sequence == seq:
        if plc.completion_result == 1:
            return ReconciliationDecision(
                ReconciliationOutcome.ALREADY_COMPLETED_DEPOSITED,
                False, False, True, True, False,
                "REGISTRAR_PALLETIZED_APENAS_SE_AINDA_NAO_REGISTRADO",
                "D760 corresponde à sequência pendente e D761=1: a unidade foi depositada; aplicar idempotência no MySQL.",
            )
        if plc.completion_result == 2:
            return ReconciliationDecision(
                ReconciliationOutcome.ALREADY_COMPLETED_REJECTED,
                False, False, False, True, False,
                "FINALIZAR_COMO_REJEITADA_SE_AINDA_PENDENTE",
                "D760 corresponde à sequência pendente e D761=2: concluir sem paletizar.",
            )
        if plc.completion_result == 3:
            return ReconciliationDecision(
                ReconciliationOutcome.ALREADY_COMPLETED_ABORTED,
                False, False, False, True, True,
                "MANTER_BLOQUEIO_E_REGISTRAR_ABORTO",
                "D760 corresponde à sequência pendente e D761=3: ciclo abortado; não criar nova identidade automaticamente.",
            )

    if plc.ack_sequence == seq and plc.machine_busy:
        return ReconciliationDecision(
            ReconciliationOutcome.PLC_STILL_PROCESSING,
            False, False, False, True, False,
            "CONTINUAR_AGUARDANDO_D760_D761",
            "O CLP conhece a mesma REQUEST_SEQUENCE e BUSY=1; não reenviar e não criar nova sequência.",
        )

    if plc.ack_sequence == seq:
        return ReconciliationDecision(
            ReconciliationOutcome.ACK_KNOWN_WAIT_COMPLETION,
            False, False, False, True, False,
            "AGUARDAR_CONCLUSAO_OU_DIAGNOSTICAR_ESTADO",
            "O CLP reconhece a sequência, porém a conclusão física ainda não foi confirmada.",
        )

    # If PLC completion points at some other non-zero sequence while our unit is
    # pending, do not guess: a human/automation diagnostic must resolve context.
    if plc.completed_sequence not in (0, seq) and plc.ack_sequence not in (0, seq):
        return ReconciliationDecision(
            ReconciliationOutcome.CONFLICT_INTERVENTION,
            False, False, False, True, True,
            "BLOQUEAR_E_REVISAR_CONTEXTO",
            "O CLP apresenta outra sequência concluída/aceita; não sobrescrever contexto nem gerar nova REQUEST_SEQUENCE.",
        )

    return ReconciliationDecision(
        ReconciliationOutcome.RESEND_SAME_SEQUENCE,
        True, False, False, True, False,
        "REENVIAR_MESMO_PACOTE_COM_MESMA_REQUEST_SEQUENCE",
        "O CLP não conhece a sequência pendente; após reconciliação é permitido reenviar exatamente a mesma identidade/payload.",
    )


class PlcTransactionStore:
    """Small persistence boundary used later by the physical Modbus adapter."""

    def get_by_unit(self, db: Session, production_unit_id: int) -> PlcTransaction | None:
        return db.scalar(select(PlcTransaction).where(PlcTransaction.production_unit_id == production_unit_id))

    def get_active_for_line(self, db: Session, line_id: int) -> PlcTransaction | None:
        return db.scalar(
            select(PlcTransaction)
            .where(PlcTransaction.line_id == line_id, PlcTransaction.status.in_(ACTIVE_TRANSACTION_STATUSES))
            .order_by(PlcTransaction.id.desc())
        )

    def persist_before_write(
        self,
        db: Session,
        *,
        line_id: int,
        production_order_id: int,
        production_unit_id: int,
        request_sequence: int,
        payload: dict,
        command: int = 1,
    ) -> PlcTransaction:
        seq = validate_request_sequence(request_sequence)
        digest = canonical_payload_hash(payload)
        existing = self.get_by_unit(db, production_unit_id)
        if existing is not None:
            if existing.request_sequence != seq or existing.payload_hash != digest:
                raise ValueError("A unidade já possui identidade Modbus persistida; REQUEST_SEQUENCE/payload não podem ser trocados.")
            return existing

        tx = PlcTransaction(
            line_id=line_id,
            production_order_id=production_order_id,
            production_unit_id=production_unit_id,
            request_sequence=seq,
            command=command,
            status="PERSISTED_PENDING",
            payload=payload,
            payload_hash=digest,
        )
        db.add(tx)
        db.flush()
        return tx


def _scenario(name: str, persisted: PersistedRequest, plc: PlcReconciliationSnapshot) -> dict:
    decision = reconcile(persisted, plc)
    return {
        "name": name,
        "persisted": asdict(persisted),
        "plc": asdict(plc),
        "decision": {**asdict(decision), "outcome": decision.outcome.value},
    }


def get_reconciliation_diagnostic() -> dict:
    pending = PersistedRequest(request_sequence=321, payload_hash="sha256:EXEMPLO")
    scenarios = [
        _scenario("CAIU_E_CLP_CONCLUIU_DEPOSITADA", pending, PlcReconciliationSnapshot(321, False, 321, 1, pallet_sequence=88, boxes_on_pallet=4)),
        _scenario("CAIU_E_CLP_AINDA_PROCESSA", pending, PlcReconciliationSnapshot(321, True, 0, 0)),
        _scenario("ACK_EXISTE_MAS_SEM_CONCLUSAO", pending, PlcReconciliationSnapshot(321, False, 0, 0, result_code=1)),
        _scenario("CLP_NAO_CONHECE_SEQUENCIA", pending, PlcReconciliationSnapshot(0, False, 0, 0)),
        _scenario("CONCLUIDA_COMO_REJEITADA", pending, PlcReconciliationSnapshot(321, False, 321, 2)),
        _scenario("CONFLITO_DE_CONTEXTO", pending, PlcReconciliationSnapshot(999, False, 999, 1)),
    ]
    return {
        "stage": "7.18",
        "status": "PERSISTENCE_IDEMPOTENCY_RECONCILIATION_READY_OFFLINE",
        "physical_connection_required": False,
        "mysql_table": "plc_transactions",
        "persist_before_write": True,
        "stable_identity": "REQUEST_SEQUENCE + payload_hash + production_unit_id",
        "restart_rule": "AO_SUBIR_RECONCILIAR_TRANSACAO_ATIVA_ANTES_DE_NOVA_ESCRITA",
        "reconnect_read_first": ["D752", "D754", "D757", "D758", "D760", "D761"],
        "idempotency_rules": [
            "Persistir REQUEST_SEQUENCE e payload antes de escrever no CLP.",
            "A mesma unidade nunca recebe nova REQUEST_SEQUENCE após restart/reconexão.",
            "D760=REQUEST_SEQUENCE e D761=1 registra PALLETIZED no máximo uma vez.",
            "Se D752=REQUEST_SEQUENCE e BUSY=1, apenas continuar aguardando.",
            "Se o CLP não conhecer a sequência, reenviar o mesmo pacote com a mesma REQUEST_SEQUENCE.",
            "Conflito de sequência bloqueia escrita automática; não adivinhar estado.",
        ],
        "scenarios": scenarios,
        "message": "Persistência MySQL, idempotência e reconciliação pós-restart preparadas offline; nenhuma conexão física é aberta nesta etapa.",
    }
