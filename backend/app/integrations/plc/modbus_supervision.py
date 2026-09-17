from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from .modbus_contract import get_modbus_contract


class CommunicationHealth(str, Enum):
    STARTING = "STARTING"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    PLC_HEARTBEAT_STALE = "PLC_HEARTBEAT_STALE"
    TRANSPORT_RETRYING = "TRANSPORT_RETRYING"
    DISCONNECTED_SAFE = "DISCONNECTED_SAFE"
    RECONNECT_RECONCILE = "RECONNECT_RECONCILE"


@dataclass(frozen=True)
class SupervisionSnapshot:
    connected: bool
    now_ms: int
    last_poll_success_ms: int | None = None
    last_pc_heartbeat_write_ms: int | None = None
    plc_heartbeat_value: int | None = None
    plc_heartbeat_last_change_ms: int | None = None
    consecutive_transport_failures: int = 0
    reconnecting: bool = False


@dataclass(frozen=True)
class SupervisionDecision:
    health: CommunicationHealth
    may_accept_new_unit: bool
    safe_state: bool
    poll_due: bool
    pc_heartbeat_due: bool
    heartbeat_stale: bool
    transport_retry_allowed: bool
    transport_attempt: int
    requires_reconciliation: bool
    next_action: str
    reason: str


def _elapsed(now_ms: int, previous_ms: int | None) -> int | None:
    if previous_ms is None:
        return None
    return max(0, now_ms - previous_ms)


def evaluate_supervision(snapshot: SupervisionSnapshot) -> SupervisionDecision:
    timing = get_modbus_contract()["timing"]
    poll_elapsed = _elapsed(snapshot.now_ms, snapshot.last_poll_success_ms)
    pc_hb_elapsed = _elapsed(snapshot.now_ms, snapshot.last_pc_heartbeat_write_ms)
    plc_hb_elapsed = _elapsed(snapshot.now_ms, snapshot.plc_heartbeat_last_change_ms)

    poll_due = poll_elapsed is None or poll_elapsed >= timing["poll_interval_ms"]
    pc_heartbeat_due = pc_hb_elapsed is None or pc_hb_elapsed >= timing["heartbeat_interval_ms"]
    heartbeat_stale = plc_hb_elapsed is not None and plc_hb_elapsed >= timing["heartbeat_stale_ms"]
    retry_max = timing["transport_retry_attempts"]
    retry_allowed = 0 < snapshot.consecutive_transport_failures < retry_max
    attempt = min(max(snapshot.consecutive_transport_failures + 1, 1), retry_max)

    if snapshot.reconnecting:
        return SupervisionDecision(
            CommunicationHealth.RECONNECT_RECONCILE,
            False,
            True,
            True,
            pc_heartbeat_due,
            heartbeat_stale,
            False,
            attempt,
            True,
            "LER_ESTADO_E_RECONCILIAR",
            "A comunicação retornou; ler o estado do CLP e reconciliar sequência/resultado antes de qualquer novo envio.",
        )

    if not snapshot.connected:
        return SupervisionDecision(
            CommunicationHealth.DISCONNECTED_SAFE,
            False,
            True,
            False,
            False,
            heartbeat_stale,
            False,
            attempt,
            True,
            "BLOQUEAR_NOVAS_UNIDADES_E_AGUARDAR_REDE",
            "Sem transporte Modbus: bloquear novas unidades e preservar qualquer sequência pendente.",
        )

    if snapshot.consecutive_transport_failures >= retry_max:
        return SupervisionDecision(
            CommunicationHealth.DISCONNECTED_SAFE,
            False,
            True,
            True,
            pc_heartbeat_due,
            heartbeat_stale,
            False,
            retry_max,
            True,
            "ENTRAR_ESTADO_SEGURO_E_RECONCILIAR_QUANDO_VOLTAR",
            "As 3 tentativas de transporte foram esgotadas; nenhuma unidade nova pode ser enviada.",
        )

    if snapshot.consecutive_transport_failures > 0:
        return SupervisionDecision(
            CommunicationHealth.TRANSPORT_RETRYING,
            False,
            True,
            True,
            pc_heartbeat_due,
            heartbeat_stale,
            retry_allowed,
            attempt,
            False,
            "REPETIR_TRANSPORTE_SEM_NOVA_REQUEST_SEQUENCE",
            "Falha de transporte em recuperação; repetir somente o transporte da mesma operação.",
        )

    if heartbeat_stale:
        return SupervisionDecision(
            CommunicationHealth.PLC_HEARTBEAT_STALE,
            False,
            True,
            True,
            pc_heartbeat_due,
            True,
            False,
            1,
            True,
            "BLOQUEAR_E_VERIFICAR_CLP",
            "D751 não mudou por 5 s ou mais; tratar o CLP como comunicação não confiável até reconciliação.",
        )

    if snapshot.last_poll_success_ms is None or snapshot.plc_heartbeat_last_change_ms is None:
        return SupervisionDecision(
            CommunicationHealth.STARTING,
            False,
            True,
            True,
            True,
            False,
            False,
            1,
            False,
            "INICIAR_POLLING_E_HEARTBEAT",
            "Supervisão iniciando: ainda não existe amostra suficiente para liberar produção automática.",
        )

    # Qualidade degradada se uma leitura ficou significativamente atrasada, mas ainda abaixo da janela stale.
    degraded_threshold = timing["poll_interval_ms"] * 4
    if poll_elapsed is not None and poll_elapsed >= degraded_threshold:
        return SupervisionDecision(
            CommunicationHealth.DEGRADED,
            False,
            True,
            True,
            pc_heartbeat_due,
            False,
            False,
            1,
            False,
            "PRIORIZAR_NOVA_LEITURA_D750_D779",
            "Polling está atrasado; bloquear nova unidade até recuperar cadência estável.",
        )

    return SupervisionDecision(
        CommunicationHealth.HEALTHY,
        True,
        False,
        poll_due,
        pc_heartbeat_due,
        False,
        False,
        1,
        False,
        "MANTER_POLLING_E_HEARTBEAT",
        "Comunicação saudável: polling e heartbeat dentro das janelas definidas pelo contrato.",
    )


def _scenario(name: str, snapshot: SupervisionSnapshot) -> dict:
    decision = evaluate_supervision(snapshot)
    return {
        "name": name,
        "snapshot": asdict(snapshot),
        "decision": {**asdict(decision), "health": decision.health.value},
    }


def get_supervision_diagnostic() -> dict:
    timing = get_modbus_contract()["timing"]
    now = 10_000
    scenarios = [
        _scenario("INICIALIZANDO", SupervisionSnapshot(True, now_ms=now)),
        _scenario("SAUDAVEL", SupervisionSnapshot(True, now_ms=now, last_poll_success_ms=9_900, last_pc_heartbeat_write_ms=9_500, plc_heartbeat_value=42, plc_heartbeat_last_change_ms=9_500)),
        _scenario("POLLING_ATRASADO", SupervisionSnapshot(True, now_ms=now, last_poll_success_ms=8_800, last_pc_heartbeat_write_ms=9_500, plc_heartbeat_value=42, plc_heartbeat_last_change_ms=9_500)),
        _scenario("HEARTBEAT_STALE", SupervisionSnapshot(True, now_ms=now, last_poll_success_ms=9_900, last_pc_heartbeat_write_ms=9_500, plc_heartbeat_value=42, plc_heartbeat_last_change_ms=5_000)),
        _scenario("RETRY_TRANSPORTE_2_DE_3", SupervisionSnapshot(True, now_ms=now, last_poll_success_ms=9_900, last_pc_heartbeat_write_ms=9_500, plc_heartbeat_value=42, plc_heartbeat_last_change_ms=9_500, consecutive_transport_failures=1)),
        _scenario("TRANSPORTE_ESGOTADO", SupervisionSnapshot(True, now_ms=now, last_poll_success_ms=9_900, last_pc_heartbeat_write_ms=9_500, plc_heartbeat_value=42, plc_heartbeat_last_change_ms=9_500, consecutive_transport_failures=3)),
        _scenario("SEM_REDE", SupervisionSnapshot(False, now_ms=now, plc_heartbeat_value=42, plc_heartbeat_last_change_ms=9_500)),
        _scenario("RECONEXAO", SupervisionSnapshot(True, now_ms=now, last_poll_success_ms=9_900, plc_heartbeat_value=43, plc_heartbeat_last_change_ms=9_900, reconnecting=True)),
    ]
    return {
        "stage": "7.17",
        "status": "COMMUNICATION_SUPERVISION_READY_OFFLINE",
        "physical_connection_required": False,
        "automatic_operation_target": True,
        "polling": {
            "range": "D750-D779",
            "interval_ms": timing["poll_interval_ms"],
            "continuous": True,
        },
        "pc_heartbeat": {
            "register": "D701",
            "interval_ms": timing["heartbeat_interval_ms"],
            "counter": "UINT16_INCREMENTING",
        },
        "plc_heartbeat": {
            "register": "D751",
            "expected_interval_ms": timing["heartbeat_interval_ms"],
            "stale_after_ms": timing["heartbeat_stale_ms"],
            "rule": "SE D751 NAO MUDAR POR 5 S, BLOQUEAR NOVAS UNIDADES",
        },
        "transport": {
            "timeout_ms": timing["transport_timeout_ms"],
            "retry_attempts": timing["transport_retry_attempts"],
            "retry_interval_ms": timing["transport_retry_interval_ms"],
            "same_request_sequence": True,
        },
        "safe_rules": [
            "Qualquer perda de comunicação bloqueia novas unidades.",
            "Heartbeat stale bloqueia produção mesmo que o socket ainda pareça conectado.",
            "Após 3 falhas de transporte entrar em estado seguro.",
            "Após reconexão reconciliar D752/D754/D757/D758/D760/D761 antes de escrever.",
            "Supervisão automática não depende de operador no fluxo normal.",
        ],
        "health_states": [state.value for state in CommunicationHealth],
        "scenarios": scenarios,
        "message": "Heartbeat, polling e supervisão Modbus preparados offline para operação autônoma. A etapa não abre conexão física com o CLP.",
    }
