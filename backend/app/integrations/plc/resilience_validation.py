from __future__ import annotations

from dataclasses import asdict, dataclass

from .automatic_production import AutomaticProductionSnapshot, evaluate_automatic_production
from .modbus_reconciliation import PersistedRequest, PlcReconciliationSnapshot, reconcile
from .modbus_supervision import SupervisionSnapshot, evaluate_supervision


@dataclass(frozen=True)
class ResilienceScenario:
    name: str
    category: str
    expected_state: str
    observed_state: str
    passed: bool
    safety_result: str
    next_action: str


def _supervision_scenario(name: str, category: str, expected: str, snapshot: SupervisionSnapshot) -> ResilienceScenario:
    decision = evaluate_supervision(snapshot)
    observed = decision.health.value
    return ResilienceScenario(
        name=name,
        category=category,
        expected_state=expected,
        observed_state=observed,
        passed=observed == expected and not decision.may_accept_new_unit,
        safety_result="NOVAS_UNIDADES_BLOQUEADAS" if not decision.may_accept_new_unit else "UNIDADE_PODE_AVANCAR",
        next_action=decision.next_action,
    )


def _reconciliation_scenario(name: str, category: str, expected: str, plc: PlcReconciliationSnapshot) -> ResilienceScenario:
    decision = reconcile(PersistedRequest(request_sequence=4321, payload_hash="sha256:7.23"), plc)
    observed = decision.outcome.value
    safe = not decision.may_create_new_sequence
    return ResilienceScenario(
        name=name,
        category=category,
        expected_state=expected,
        observed_state=observed,
        passed=observed == expected and safe,
        safety_result="MESMA_SEQUENCE_PRESERVADA" if decision.same_request_sequence_required else "CONTEXTO_BLOQUEADO",
        next_action=decision.next_action,
    )


def _production_scenario(name: str, category: str, expected: str, snapshot: AutomaticProductionSnapshot) -> ResilienceScenario:
    decision = evaluate_automatic_production(snapshot)
    observed = decision.state.value
    return ResilienceScenario(
        name=name,
        category=category,
        expected_state=expected,
        observed_state=observed,
        passed=observed == expected and not decision.release_next_read,
        safety_result="PROXIMO_QR_BLOQUEADO" if not decision.release_next_read else "PROXIMO_QR_LIBERADO",
        next_action=decision.next_action,
    )


def get_resilience_validation_diagnostic() -> dict:
    now = 10_000
    scenarios = [
        _supervision_scenario(
            "QUEDA_DE_COMUNICACAO",
            "COMUNICACAO",
            "DISCONNECTED_SAFE",
            SupervisionSnapshot(False, now_ms=now, plc_heartbeat_value=10, plc_heartbeat_last_change_ms=9_900),
        ),
        _supervision_scenario(
            "TIMEOUT_TRANSPORTE_EM_RETRY",
            "TIMEOUT",
            "TRANSPORT_RETRYING",
            SupervisionSnapshot(True, now_ms=now, last_poll_success_ms=9_900, last_pc_heartbeat_write_ms=9_500, plc_heartbeat_value=10, plc_heartbeat_last_change_ms=9_500, consecutive_transport_failures=1),
        ),
        _supervision_scenario(
            "RETENTATIVAS_ESGOTADAS",
            "TIMEOUT",
            "DISCONNECTED_SAFE",
            SupervisionSnapshot(True, now_ms=now, last_poll_success_ms=9_900, last_pc_heartbeat_write_ms=9_500, plc_heartbeat_value=10, plc_heartbeat_last_change_ms=9_500, consecutive_transport_failures=3),
        ),
        _supervision_scenario(
            "HEARTBEAT_CLP_STALE",
            "HEARTBEAT",
            "PLC_HEARTBEAT_STALE",
            SupervisionSnapshot(True, now_ms=now, last_poll_success_ms=9_900, last_pc_heartbeat_write_ms=9_500, plc_heartbeat_value=10, plc_heartbeat_last_change_ms=5_000),
        ),
        _supervision_scenario(
            "RECONEXAO_EXIGE_RECONCILIACAO",
            "RECONEXAO",
            "RECONNECT_RECONCILE",
            SupervisionSnapshot(True, now_ms=now, last_poll_success_ms=9_900, plc_heartbeat_value=11, plc_heartbeat_last_change_ms=9_900, reconnecting=True),
        ),
        _reconciliation_scenario(
            "RESTART_CLP_JA_CONCLUIU",
            "RESTART",
            "ALREADY_COMPLETED_DEPOSITED",
            PlcReconciliationSnapshot(4321, False, 4321, 1, result_code=1, pallet_sequence=55, boxes_on_pallet=7),
        ),
        _reconciliation_scenario(
            "CLP_NAO_CONHECE_PEDIDO_APOS_RETORNO",
            "RECONEXAO",
            "RESEND_SAME_SEQUENCE",
            PlcReconciliationSnapshot(0, False, 0, 0),
        ),
        _reconciliation_scenario(
            "SEQUENCIA_DIVERGENTE",
            "DUPLICIDADE_CONFLITO",
            "CONFLICT_INTERVENTION",
            PlcReconciliationSnapshot(999, False, 999, 1),
        ),
        _production_scenario(
            "CLP_REPORTA_SEQUENCIA_DUPLICADA",
            "DUPLICIDADE",
            "BLOCKED_INTERVENTION",
            AutomaticProductionSnapshot(
                communication_healthy=True,
                machine_ready=True,
                pending_sequence=4321,
                transaction_persisted=True,
                payload_written=True,
                trigger_written=True,
                ack_sequence=4321,
                result_code=3,
            ),
        ),
        _production_scenario(
            "CICLO_ABORTADO_NAO_PALETIZA",
            "ABORTO",
            "BLOCKED_INTERVENTION",
            AutomaticProductionSnapshot(
                communication_healthy=True,
                machine_ready=True,
                pending_sequence=4321,
                completed_sequence=4321,
                completion_result=3,
            ),
        ),
    ]

    data = [asdict(item) for item in scenarios]
    passed = sum(1 for item in scenarios if item.passed)
    return {
        "stage": "7.23",
        "status": "RESILIENCE_FAILURE_MATRIX_VALIDATED_OFFLINE" if passed == len(scenarios) else "RESILIENCE_VALIDATION_ATTENTION",
        "physical_connection_required": False,
        "physical_socket_opened": False,
        "scenario_count": len(scenarios),
        "passed_count": passed,
        "failed_count": len(scenarios) - passed,
        "all_passed": passed == len(scenarios),
        "categories": ["COMUNICACAO", "TIMEOUT", "HEARTBEAT", "RECONEXAO", "RESTART", "DUPLICIDADE", "ABORTO"],
        "invariants": [
            "Falha de comunicação bloqueia novas unidades.",
            "Retry de transporte mantém a mesma REQUEST_SEQUENCE.",
            "Timeout do ciclo físico nunca autoriza nova sequência automaticamente.",
            "Após reconexão/restart, reconciliar o estado antes de escrever.",
            "D760/D761 evita dupla contabilização após restart.",
            "Sequência duplicada/conflitante nunca é tratada como paletização válida.",
            "Ciclo abortado nunca incrementa produção confirmada.",
        ],
        "scenarios": data,
        "message": "Matriz offline de resiliência validada para falhas, timeout, heartbeat, reconexão, restart, duplicidade e aborto; nenhuma conexão física é aberta nesta etapa.",
    }
