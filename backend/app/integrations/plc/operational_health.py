from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from .automatic_production import get_automatic_production_diagnostic
from .industrial_diagnostics import get_industrial_diagnostics
from .modbus_physical import get_physical_adapter_diagnostic
from .modbus_simulator import get_simulator_diagnostic
from .resilience_validation import get_resilience_validation_diagnostic


def _check(name: str, status: str, ok: bool, detail: str, blocking: bool = False) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "ok": ok,
        "blocking": blocking,
        "detail": detail,
    }


def get_operational_health(db: Session) -> dict[str, Any]:
    """ETAPA 7.25 — autodiagnóstico operacional 100% offline.

    Não abre socket Modbus e não tenta alcançar o CLP físico. O adaptador físico
    bloqueado é esperado nesta fase e, por isso, não degrada a saúde offline.
    """
    db.execute(text("SELECT 1"))

    automatic = get_automatic_production_diagnostic()
    simulator = get_simulator_diagnostic()
    resilience = get_resilience_validation_diagnostic()
    industrial = get_industrial_diagnostics(db)
    physical = get_physical_adapter_diagnostic()

    checks = [
        _check("BACKEND_API", "ONLINE", True, "API respondeu ao autodiagnóstico."),
        _check("MYSQL", "ONLINE", True, "SELECT 1 executado com sucesso."),
        _check(
            "AUTOMATIC_ENGINE",
            "READY_OFFLINE",
            bool(automatic.get("physical_connection_required") is False),
            "Motor automático preparado para o fluxo sem operador em ambiente offline.",
        ),
        _check(
            "PLC_SIMULATOR",
            "READY",
            bool(simulator.get("physical_socket_opened") is False),
            "Simulador D700-D763 disponível sem socket físico.",
        ),
        _check(
            "RESILIENCE_MATRIX",
            "PASS" if resilience.get("all_passed") else "ATTENTION",
            bool(resilience.get("all_passed")),
            f"{resilience.get('passed_count', 0)}/{resilience.get('scenario_count', 0)} cenários aprovados.",
            blocking=not bool(resilience.get("all_passed")),
        ),
        _check(
            "PENDING_TRANSACTIONS",
            "CLEAR" if industrial.get("pending_transaction_count", 0) == 0 else "ATTENTION",
            industrial.get("pending_transaction_count", 0) == 0,
            f"{industrial.get('pending_transaction_count', 0)} transação(ões) pendente(s) para reconciliação/fechamento.",
            blocking=industrial.get("pending_transaction_count", 0) > 0,
        ),
        _check(
            "PHYSICAL_ADAPTER",
            "BLOCKED_EXPECTED",
            bool(physical.get("physical_socket_opened") is False),
            "Conexão real permanece bloqueada nesta etapa; nenhuma tentativa contra o CLP é permitida.",
        ),
    ]

    failed = [item for item in checks if not item["ok"]]
    blocking = [item for item in checks if item["blocking"] and not item["ok"]]

    return {
        "stage": "7.25",
        "status": "HEALTHY_OFFLINE" if not blocking else "DEGRADED_OFFLINE",
        "physical_connection_required": False,
        "physical_socket_opened": False,
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "blocking_count": len(blocking),
        "accept_new_simulated_unit": len(blocking) == 0,
        "real_machine_release_allowed": False,
        "checks": checks,
        "safety": [
            "Autodiagnóstico não abre socket Modbus físico.",
            "Falha bloqueante impede aceite de nova unidade no fluxo simulado.",
            "Adaptador físico bloqueado é condição esperada antes do comissionamento.",
            "Liberação da máquina real continua proibida nesta etapa.",
        ],
        "message": "Health-check operacional e autodiagnóstico disponíveis offline antes de aceitar novas unidades.",
    }
