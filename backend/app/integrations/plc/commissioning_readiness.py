from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from .industrial_diagnostics import get_industrial_diagnostics
from .modbus_contract import get_modbus_contract
from .modbus_physical import get_physical_adapter_diagnostic
from .operational_health import get_operational_health
from .resilience_validation import get_resilience_validation_diagnostic


def _item(code: str, title: str, category: str, status: str, detail: str, blocking_real: bool) -> dict[str, Any]:
    return {
        "code": code,
        "title": title,
        "category": category,
        "status": status,
        "detail": detail,
        "blocking_real": blocking_real,
    }


def get_commissioning_readiness(db: Session) -> dict[str, Any]:
    """ETAPA 7.26 — gate de prontidão pré-comissionamento, sem conexão física."""
    contract = get_modbus_contract()
    health = get_operational_health(db)
    resilience = get_resilience_validation_diagnostic()
    industrial = get_industrial_diagnostics(db)
    physical = get_physical_adapter_diagnostic()

    pending_automation = list(contract.get("pending_automation", []))
    commissioning = list(physical.get("pending_commissioning", []))
    ladder_ready = bool(physical.get("commissioning_gates", {}).get("ISPsoft_COMPILE"))

    checklist = [
        _item(
            "OFFLINE_HEALTH",
            "Saúde operacional offline",
            "SOFTWARE",
            "READY" if health.get("status") == "HEALTHY_OFFLINE" else "BLOCKED",
            f"Health-check: {health.get('passed_count', 0)}/{health.get('check_count', 0)} aprovado(s).",
            health.get("status") != "HEALTHY_OFFLINE",
        ),
        _item(
            "RESILIENCE",
            "Matriz de resiliência",
            "SOFTWARE",
            "READY" if resilience.get("all_passed") else "BLOCKED",
            f"Resiliência: {resilience.get('passed_count', 0)}/{resilience.get('scenario_count', 0)} cenário(s) aprovado(s).",
            not bool(resilience.get("all_passed")),
        ),
        _item(
            "PENDING_TRANSACTIONS",
            "Transações pendentes",
            "SOFTWARE",
            "READY" if industrial.get("pending_transaction_count", 0) == 0 else "BLOCKED",
            f"{industrial.get('pending_transaction_count', 0)} transação(ões) aguardando reconciliação/fechamento.",
            industrial.get("pending_transaction_count", 0) > 0,
        ),
        _item(
            "PHYSICAL_ADAPTER",
            "Adaptador físico protegido",
            "SAFETY",
            "SAFE_BLOCKED" if not physical.get("physical_socket_opened") else "UNSAFE",
            "Socket físico permanece fechado antes do comissionamento.",
            bool(physical.get("physical_socket_opened")),
        ),
        _item(
            "LADDER_REV04_ISPSOFT",
            "Ladder Rev.06 no ISPSoft",
            "AUTOMATION",
            "READY" if ladder_ready else "PENDING_AUTOMATION",
            "Rev.06 compilada/comparada no ISPSoft." if ladder_ready else "Abrir, compilar e comparar a Rev.06 no ISPSoft antes do download e do teste físico.",
            not ladder_ready,
        ),
        _item(
            "AUTOMATION_TABLES",
            "Tabelas e IDs da automação",
            "AUTOMATION",
            "PENDING_AUTOMATION" if pending_automation else "READY",
            ", ".join(pending_automation) if pending_automation else "Sem pendências de automação.",
            bool(pending_automation),
        ),
        _item(
            "COMMISSIONING_VALIDATIONS",
            "Validações exclusivas de comissionamento",
            "COMMISSIONING",
            "PENDING_COMMISSIONING" if commissioning else "READY",
            ", ".join(commissioning) if commissioning else "Sem validações pendentes de comissionamento.",
            bool(commissioning),
        ),
    ]

    ready = [item for item in checklist if item["status"] in {"READY", "SAFE_BLOCKED"}]
    real_blockers = [item for item in checklist if item["blocking_real"]]

    return {
        "stage": "7.26",
        "status": "READY_FOR_OFFLINE_CONTINUATION" if health.get("status") == "HEALTHY_OFFLINE" else "OFFLINE_ATTENTION",
        "physical_connection_required": False,
        "physical_socket_opened": False,
        "offline_development_allowed": health.get("status") == "HEALTHY_OFFLINE",
        "real_commissioning_allowed": len(real_blockers) == 0,
        "checklist_count": len(checklist),
        "ready_count": len(ready),
        "real_blocker_count": len(real_blockers),
        "pending_automation_count": len(pending_automation) + (0 if ladder_ready else 1),
        "pending_commissioning_count": len(commissioning),
        "pending_automation": pending_automation,
        "pending_commissioning": commissioning,
        "checklist": checklist,
        "next_offline_focus": "Continuar preparação de software sem abrir socket físico.",
        "factory_gate": "Só liberar conexão real após ladder implementado, pendências da automação fechadas e validações de comissionamento executadas.",
        "message": "Gate de prontidão pré-comissionamento consolidado; desenvolvimento offline pode continuar com CLP real bloqueado.",
    }
