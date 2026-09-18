from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.database.session import get_db
from app.models.user import User
from app.schemas.retest import RetestAttemptRead, RetestDiagnosticStatus, RetestSimulationRequest, RetestSimulationResponse, RetestUnitRead, ReworkOrderCreate, ReworkOrderRead
from app.services.audit_service import write_audit
from app.services.retest_service import RetestService


router = APIRouter(prefix="/retests", tags=["Retests"])
service = RetestService()


@router.get("/status", response_model=RetestDiagnosticStatus)
def retest_status(_: User = Depends(require_roles("SUPERVISOR", "ADMIN"))):
    return service.diagnostic_status()


@router.get("/units", response_model=list[RetestUnitRead])
def retest_units(
    query: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("SUPERVISOR", "ADMIN")),
):
    units = service.search_units(db, query, limit)
    write_audit(db, "RETEST_UNITS_VIEWED", actor, "RETEST_UNIT_SEARCH", None, {
        "query": query,
        "returned": len(units),
        "offline_only": True,
    })
    return units


@router.get("", response_model=list[RetestAttemptRead])
def retest_history(
    serial_number: str = Query(..., min_length=1, max_length=100),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("SUPERVISOR", "ADMIN")),
):
    attempts = service.list_for_serial(db, serial_number)
    write_audit(db, "RETEST_HISTORY_VIEWED", actor, "PRODUCTION_UNIT_SERIAL", serial_number, {
        "attempt_count": len(attempts),
        "offline_only": True,
    })
    return attempts


@router.post("/simulate", response_model=RetestSimulationResponse)
def simulate_retest(
    payload: RetestSimulationRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("SUPERVISOR", "ADMIN")),
):
    attempt, replayed = service.simulate(db, payload, actor.username)
    if not replayed:
        write_audit(
            db,
            "RETEST_SIMULATED",
            actor,
            "RETEST_ATTEMPT",
            attempt.id,
            {
                "production_unit_id": attempt.production_unit_id,
                "attempt_number": attempt.attempt_number,
                "decision": attempt.decision,
                "counted_in_production": False,
            },
        )
    return {
        "attempt": attempt,
        "replayed": replayed,
        "production_state_changed": False,
        "message": "Tentativa existente recuperada sem duplicação." if replayed else "Tentativa simulada registrada sem alterar a produção.",
    }


@router.post("/rework-orders", response_model=ReworkOrderRead)
def create_rework_order(
    payload: ReworkOrderCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("SUPERVISOR", "ADMIN")),
):
    item = service.create_rework_order(db, payload.serial_number, payload.reason, actor.username)
    write_audit(db, "REWORK_ORDER_OPENED", actor, "REWORK_ORDER", item.id, {
        "original_production_unit_id": item.original_production_unit_id,
        "reason": item.reason,
    })
    return item
