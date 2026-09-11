from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from .commissioning_plan import get_commissioning_plan
from .commissioning_readiness import get_commissioning_readiness
from .operational_health import get_operational_health
from .resilience_validation import get_resilience_validation_diagnostic


def get_commissioning_evidence_package(db: Session) -> dict[str, Any]:
    """ETAPA 7.28 — manifesto/checklist de evidências, 100% offline e sem socket físico."""
    plan = get_commissioning_plan(db)
    readiness = get_commissioning_readiness(db)
    health = get_operational_health(db)
    resilience = get_resilience_validation_diagnostic()

    evidence_items: list[dict[str, Any]] = []
    for step in plan["steps"]:
        if step["phase"] == "OFFLINE":
            state = "PREPARED" if step["status"] == "READY" else "BLOCKED"
        elif step["phase"] == "AUTOMATION":
            state = "WAIT_AUTOMATION" if step["status"] != "READY" else "PREPARED"
        else:
            state = "WAIT_FACTORY"
        evidence_items.append({
            "code": step["code"],
            "order": step["order"],
            "title": step["title"],
            "phase": step["phase"],
            "state": state,
            "expected_evidence": step["evidence"],
            "capture_template": (
                "Registrar data/hora, responsável, resultado PASS/FAIL, observação e referência do log/print."
            ),
            "requires_machine": step["requires_machine"],
        })

    prepared_count = sum(1 for item in evidence_items if item["state"] == "PREPARED")
    wait_automation_count = sum(1 for item in evidence_items if item["state"] == "WAIT_AUTOMATION")
    wait_factory_count = sum(1 for item in evidence_items if item["state"] == "WAIT_FACTORY")
    blocked_count = sum(1 for item in evidence_items if item["state"] == "BLOCKED")

    offline_snapshot = [
        {"code": "HEALTH_725", "label": "Health-check operacional", "value": health.get("status", "UNKNOWN")},
        {"code": "RESILIENCE_723", "label": "Matriz de resiliência", "value": "PASS" if resilience.get("all_passed") else "ATTENTION"},
        {"code": "READINESS_726", "label": "Gate pré-comissionamento", "value": readiness.get("status", "UNKNOWN")},
        {"code": "PLAN_727", "label": "Plano de comissionamento", "value": plan.get("status", "UNKNOWN")},
    ]

    return {
        "stage": "7.28",
        "status": "EVIDENCE_PACKAGE_READY_OFFLINE" if blocked_count == 0 else "OFFLINE_ATTENTION",
        "physical_connection_required": False,
        "physical_socket_opened": bool(plan.get("physical_socket_opened", False)),
        "real_execution_allowed": bool(plan.get("real_release_allowed", False)),
        "evidence_count": len(evidence_items),
        "prepared_count": prepared_count,
        "wait_automation_count": wait_automation_count,
        "wait_factory_count": wait_factory_count,
        "blocked_count": blocked_count,
        "offline_snapshot": offline_snapshot,
        "items": evidence_items,
        "required_fields": ["data_hora", "responsavel", "resultado", "observacao", "referencia_evidencia"],
        "acceptance_rule": "Cada passo da 7.27 deve possuir evidência PASS antes de avançar; FAIL ou divergência aplica STOP e exige análise antes da continuidade.",
        "retention_rule": "Evidências devem permanecer vinculadas à versão/baseline do software e ao comissionamento correspondente; política definitiva de retenção continua configurável.",
        "next_offline_focus": "Preparar baseline/versionamento e pacote de entrega para fábrica; não habilitar PLC_PHYSICAL_ENABLED antes da autorização e fechamento dos gates.",
        "message": "Checklist e manifesto de evidências preparados offline; itens de automação/fábrica permanecem pendentes e nenhum socket físico foi aberto.",
    }
