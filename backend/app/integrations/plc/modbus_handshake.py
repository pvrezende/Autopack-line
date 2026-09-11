from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from .modbus_contract import get_modbus_contract


class HandshakeState(str, Enum):
    IDLE = "IDLE"
    PRECHECK_BLOCKED = "PRECHECK_BLOCKED"
    READY_TO_WRITE_PAYLOAD = "READY_TO_WRITE_PAYLOAD"
    READY_TO_TRIGGER = "READY_TO_TRIGGER"
    WAITING_ACK = "WAITING_ACK"
    REQUEST_ACCEPTED = "REQUEST_ACCEPTED"
    WAITING_CYCLE_COMPLETION = "WAITING_CYCLE_COMPLETION"
    COMPLETED_PLACED = "COMPLETED_PLACED"
    COMPLETED_REJECTED = "COMPLETED_REJECTED"
    COMPLETED_ABORTED = "COMPLETED_ABORTED"
    ACK_TIMEOUT_SAFE = "ACK_TIMEOUT_SAFE"
    CYCLE_TIMEOUT_INTERVENTION = "CYCLE_TIMEOUT_INTERVENTION"
    TRANSPORT_RETRY = "TRANSPORT_RETRY"
    COMMUNICATION_LOST = "COMMUNICATION_LOST"
    RECONNECT_RECONCILE = "RECONNECT_RECONCILE"


@dataclass(frozen=True)
class MachineSnapshot:
    connected: bool
    machine_ready: bool = False
    machine_busy: bool = False
    machine_fault: bool = False
    maintenance_mode: bool = False
    ack_sequence: int = 0
    result_code: int = 0
    completed_sequence: int = 0
    completion_result: int = 0


@dataclass(frozen=True)
class HandshakeDecision:
    state: HandshakeState
    may_send_new_unit: bool
    may_write_payload: bool
    may_trigger_command: bool
    may_mark_palletized: bool
    automatic_resend_allowed: bool
    requires_intervention: bool
    next_action: str
    reason: str


def evaluate_handshake(
    snapshot: MachineSnapshot,
    *,
    pending_sequence: int | None = None,
    payload_written: bool = False,
    trigger_written: bool = False,
    ack_elapsed_ms: int = 0,
    cycle_elapsed_ms: int = 0,
    transport_failed: bool = False,
    reconnecting: bool = False,
) -> HandshakeDecision:
    timing = get_modbus_contract()["timing"]

    if not snapshot.connected:
        return HandshakeDecision(
            HandshakeState.COMMUNICATION_LOST, False, False, False, False, False, True,
            "BLOQUEAR_LEITURA_E_AGUARDAR_RECONEXAO",
            "Sem comunicação com o CLP: nenhuma nova unidade pode ser enviada.",
        )

    if reconnecting:
        return HandshakeDecision(
            HandshakeState.RECONNECT_RECONCILE, False, False, False, False, False, False,
            "LER_ESTADO_ANTES_DE_ESCREVER",
            "Após reconexão, reconciliar D752/D754/D757/D758/D760/D761 antes de qualquer escrita.",
        )

    if pending_sequence:
        if snapshot.completed_sequence == pending_sequence:
            if snapshot.completion_result == 1:
                return HandshakeDecision(
                    HandshakeState.COMPLETED_PLACED, False, False, False, True, False, False,
                    "REGISTRAR_PALLETIZED_IDEMPOTENTE",
                    "Conclusão física confirmada: D760 corresponde à sequência e D761=1.",
                )
            if snapshot.completion_result == 2:
                return HandshakeDecision(
                    HandshakeState.COMPLETED_REJECTED, True, False, False, False, False, False,
                    "REGISTRAR_REJEICAO_E_LIBERAR_PROXIMA",
                    "CLP concluiu a sequência como rejeitada (D761=2).",
                )
            if snapshot.completion_result == 3:
                return HandshakeDecision(
                    HandshakeState.COMPLETED_ABORTED, False, False, False, False, False, True,
                    "REGISTRAR_ABORTO_E_SOLICITAR_INTERVENCAO",
                    "CLP concluiu a sequência como abortada (D761=3).",
                )

        if transport_failed:
            return HandshakeDecision(
                HandshakeState.TRANSPORT_RETRY, False, False, False, False, True, False,
                "REPETIR_TRANSPORTE_MESMA_OPERACAO",
                "Falha de transporte Modbus permite até 3 tentativas; não criar nova REQUEST_SEQUENCE.",
            )

        if trigger_written and snapshot.ack_sequence != pending_sequence:
            if ack_elapsed_ms >= timing["ack_timeout_ms"]:
                return HandshakeDecision(
                    HandshakeState.ACK_TIMEOUT_SAFE, False, False, False, False, False, True,
                    "BLOQUEAR_E_RECONCILIAR",
                    "Timeout do ACK: não assumir que o CLP desconhece o pedido e não gerar nova sequência.",
                )
            return HandshakeDecision(
                HandshakeState.WAITING_ACK, False, False, False, False, False, False,
                "AGUARDAR_D752_E_D753",
                "Aguardando eco de REQUEST_SEQUENCE em D752 e resultado em D753.",
            )

        if snapshot.ack_sequence == pending_sequence:
            if snapshot.result_code == 1:
                if cycle_elapsed_ms >= timing["physical_cycle_timeout_ms"]:
                    return HandshakeDecision(
                        HandshakeState.CYCLE_TIMEOUT_INTERVENTION, False, False, False, False, False, True,
                        "INTERVENCAO_SEM_REENVIO_AUTOMATICO",
                        "Timeout do ciclo físico: o contrato proíbe reenvio automático da unidade.",
                    )
                if snapshot.machine_busy:
                    return HandshakeDecision(
                        HandshakeState.WAITING_CYCLE_COMPLETION, False, False, False, False, False, False,
                        "AGUARDAR_D760_D761",
                        "Pedido aceito e máquina ocupada; aguardar conclusão física.",
                    )
                return HandshakeDecision(
                    HandshakeState.REQUEST_ACCEPTED, False, False, False, False, False, False,
                    "AGUARDAR_EXECUCAO_DO_CICLO",
                    "Pedido aceito pelo CLP; aceite não significa paletização.",
                )
            if snapshot.result_code in {2, 3, 4, 5, 7}:
                return HandshakeDecision(
                    HandshakeState.PRECHECK_BLOCKED, False, False, False, False, False, True,
                    "TRATAR_RESULTADO_CLP",
                    f"CLP respondeu código {snapshot.result_code}; não confirmar paletização.",
                )

        if payload_written and not trigger_written:
            return HandshakeDecision(
                HandshakeState.READY_TO_TRIGGER, False, False, True, False, False, False,
                "GRAVAR_D700_D703_COM_COMMAND_1",
                "Payload D704-D749 já escrito; agora pode disparar D700-D703.",
            )

        if not payload_written:
            return HandshakeDecision(
                HandshakeState.READY_TO_WRITE_PAYLOAD, False, True, False, False, False, False,
                "GRAVAR_D704_D749",
                "Sequência pendente criada; payload deve ser escrito antes do comando.",
            )

    if snapshot.maintenance_mode:
        return HandshakeDecision(
            HandshakeState.PRECHECK_BLOCKED, False, False, False, False, False, True,
            "AGUARDAR_SAIDA_MANUTENCAO", "Máquina em modo de manutenção.",
        )
    if snapshot.machine_fault:
        return HandshakeDecision(
            HandshakeState.PRECHECK_BLOCKED, False, False, False, False, False, True,
            "AGUARDAR_LIMPEZA_FALHA", "Máquina com falha ativa.",
        )
    if snapshot.machine_busy:
        return HandshakeDecision(
            HandshakeState.PRECHECK_BLOCKED, False, False, False, False, False, False,
            "AGUARDAR_MAQUINA_LIVRE", "Máquina ocupada: não enviar nova unidade enquanto BUSY=1.",
        )
    if not snapshot.machine_ready:
        return HandshakeDecision(
            HandshakeState.PRECHECK_BLOCKED, False, False, False, False, False, False,
            "AGUARDAR_READY", "Máquina ainda não está pronta.",
        )

    return HandshakeDecision(
        HandshakeState.IDLE, True, False, False, False, False, False,
        "ACEITAR_PROXIMA_LEITURA", "READY=1, BUSY=0 e FAULT=0: nova unidade pode ser preparada.",
    )


def _scenario(name: str, snapshot: MachineSnapshot, **kwargs) -> dict:
    decision = evaluate_handshake(snapshot, **kwargs)
    return {"name": name, "snapshot": asdict(snapshot), "decision": {**asdict(decision), "state": decision.state.value}}


def get_handshake_diagnostic() -> dict:
    seq = 1234
    scenarios = [
        _scenario("MAQUINA_PRONTA", MachineSnapshot(True, machine_ready=True)),
        _scenario("MAQUINA_OCUPADA", MachineSnapshot(True, machine_ready=True, machine_busy=True)),
        _scenario("PAYLOAD_ANTES_DO_DISPARO", MachineSnapshot(True, machine_ready=True), pending_sequence=seq),
        _scenario("DISPARO_APOS_PAYLOAD", MachineSnapshot(True, machine_ready=True), pending_sequence=seq, payload_written=True),
        _scenario("AGUARDANDO_ACK", MachineSnapshot(True, machine_ready=False), pending_sequence=seq, payload_written=True, trigger_written=True, ack_elapsed_ms=500),
        _scenario("ACEITO_NAO_PALETIZADO", MachineSnapshot(True, machine_busy=True, ack_sequence=seq, result_code=1), pending_sequence=seq, payload_written=True, trigger_written=True),
        _scenario("CONCLUSAO_FISICA", MachineSnapshot(True, machine_ready=True, ack_sequence=seq, result_code=6, completed_sequence=seq, completion_result=1), pending_sequence=seq, payload_written=True, trigger_written=True),
        _scenario("TIMEOUT_CICLO_SEM_REENVIO", MachineSnapshot(True, machine_busy=True, ack_sequence=seq, result_code=1), pending_sequence=seq, payload_written=True, trigger_written=True, cycle_elapsed_ms=120000),
        _scenario("RECONEXAO", MachineSnapshot(True), pending_sequence=seq, reconnecting=True),
        _scenario("SEM_COMUNICACAO", MachineSnapshot(False), pending_sequence=seq),
    ]
    return {
        "stage": "7.16",
        "status": "HANDSHAKE_STATE_MACHINE_READY_OFFLINE",
        "physical_connection_required": False,
        "automatic_operation_target": True,
        "states": [state.value for state in HandshakeState],
        "preconditions": ["CONNECTED=1", "READY=1", "BUSY=0", "FAULT=0", "MAINTENANCE=0"],
        "write_flow": ["CRIAR_REQUEST_SEQUENCE", "D704-D749", "D700-D703_COMMAND_1", "AGUARDAR_D752_D753", "AGUARDAR_D760_D761", "D703_ZERO"],
        "palletized_rule": "D760 == REQUEST_SEQUENCE AND D761 == 1",
        "ack_is_not_palletized": True,
        "physical_cycle_timeout_auto_resend": False,
        "transport_retry_same_sequence": True,
        "new_unit_while_busy": False,
        "scenarios": scenarios,
        "message": "Máquina de estados do handshake real preparada offline. O fluxo automático diferencia aceite do CLP, execução física e confirmação final de paletização.",
    }
