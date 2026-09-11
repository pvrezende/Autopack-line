from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from .commissioning_evidence import get_commissioning_evidence_package
from .commissioning_plan import get_commissioning_plan
from .commissioning_readiness import get_commissioning_readiness
from .operational_health import get_operational_health
from .resilience_validation import get_resilience_validation_diagnostic


def get_commissioning_rehearsal(db: Session) -> dict[str, Any]:
    """ETAPA 7.29 — ensaio geral offline do comissionamento, sem socket físico."""
    health = get_operational_health(db)
    readiness = get_commissioning_readiness(db)
    plan = get_commissioning_plan(db)
    evidence = get_commissioning_evidence_package(db)
    resilience = get_resilience_validation_diagnostic()

    checks = [
        {
            "code": "BASELINE_HEALTH",
            "label": "Health-check operacional",
            "result": "PASS" if health.get("status") == "HEALTHY_OFFLINE" else "FAIL",
            "detail": health.get("status", "UNKNOWN"),
        },
        {
            "code": "RESILIENCE_MATRIX",
            "label": "Matriz de resiliência",
            "result": "PASS" if resilience.get("failed_count", 1) == 0 else "FAIL",
            "detail": f"{resilience.get('passed_count', 0)}/{resilience.get('scenario_count', 0)} cenários",
        },
        {
            "code": "OFFLINE_GATE",
            "label": "Gate para desenvolvimento offline",
            "result": "PASS" if readiness.get("offline_development_allowed") else "FAIL",
            "detail": "LIBERADO" if readiness.get("offline_development_allowed") else "BLOQUEADO",
        },
        {
            "code": "REAL_GATE",
            "label": "Gate para comissionamento real",
            "result": "WAIT" if not readiness.get("real_commissioning_allowed") else "PASS",
            "detail": "BLOQUEADO COMO ESPERADO" if not readiness.get("real_commissioning_allowed") else "LIBERADO",
        },
        {
            "code": "PLAN_ORDER",
            "label": "Plano ordenado de comissionamento",
            "result": "PASS" if plan.get("status") == "PLAN_READY_OFFLINE" and plan.get("step_count", 0) > 0 else "FAIL",
            "detail": f"{plan.get('step_count', 0)} passos",
        },
        {
            "code": "EVIDENCE_MANIFEST",
            "label": "Manifesto de evidências",
            "result": "PASS" if evidence.get("status") == "EVIDENCE_PACKAGE_READY_OFFLINE" else "FAIL",
            "detail": f"{evidence.get('evidence_count', 0)} itens",
        },
        {
            "code": "PHYSICAL_SOCKET",
            "label": "Socket Modbus físico",
            "result": "PASS" if not evidence.get("physical_socket_opened") else "FAIL",
            "detail": "NÃO ABERTO" if not evidence.get("physical_socket_opened") else "ABERTO INDEVIDAMENTE",
        },
    ]

    fail_count = sum(1 for item in checks if item["result"] == "FAIL")
    pass_count = sum(1 for item in checks if item["result"] == "PASS")
    wait_count = sum(1 for item in checks if item["result"] == "WAIT")

    rehearsal_steps: list[dict[str, Any]] = []
    for item in evidence.get("items", []):
        state = item.get("state")
        if state == "PREPARED":
            rehearsal_state = "DRY_RUN_READY"
        elif state == "WAIT_AUTOMATION":
            rehearsal_state = "WAIT_AUTOMATION"
        elif state == "WAIT_FACTORY":
            rehearsal_state = "WAIT_FACTORY"
        else:
            rehearsal_state = "BLOCKED"
        rehearsal_steps.append({
            "code": item.get("code"),
            "order": item.get("order"),
            "title": item.get("title"),
            "phase": item.get("phase"),
            "state": rehearsal_state,
            "expected_evidence": item.get("expected_evidence"),
            "requires_machine": item.get("requires_machine", False),
        })

    dry_run_ready_count = sum(1 for item in rehearsal_steps if item["state"] == "DRY_RUN_READY")
    factory_wait_count = sum(1 for item in rehearsal_steps if item["state"] == "WAIT_FACTORY")
    automation_wait_count = sum(1 for item in rehearsal_steps if item["state"] == "WAIT_AUTOMATION")

    status = "REHEARSAL_READY_OFFLINE" if fail_count == 0 else "REHEARSAL_ATTENTION"

    return {
        "stage": "7.29",
        "status": status,
        "physical_connection_required": False,
        "physical_socket_opened": False,
        "real_execution_allowed": bool(readiness.get("real_commissioning_allowed")),
        "check_count": len(checks),
        "pass_count": pass_count,
        "wait_count": wait_count,
        "fail_count": fail_count,
        "checks": checks,
        "step_count": len(rehearsal_steps),
        "dry_run_ready_count": dry_run_ready_count,
        "wait_automation_count": automation_wait_count,
        "wait_factory_count": factory_wait_count,
        "steps": rehearsal_steps,
        "execution_sequence": [step.get("code") for step in rehearsal_steps],
        "stop_rule": "Qualquer FAIL, divergência de sequência, heartbeat, offset, byte order, estado da máquina ou evidência inconsistente interrompe o comissionamento antes de nova escrita.",
        "factory_handoff": "Levar este roteiro e o pacote 7.28 para a máquina; executar somente após autorização, ladder disponível e fechamento das pendências da automação.",
        "message": "Ensaio geral offline concluído: baseline, resiliência, gate, plano e evidências consolidados sem abrir socket Modbus físico.",
    }
