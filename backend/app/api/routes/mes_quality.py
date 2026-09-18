from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.database.session import get_db
from app.models.user import User
from app.schemas.mes_quality import MesQualityResultCreate, RemovalConfirmation
from app.services.audit_service import write_audit
from app.services.mes_quality_service import MesQualityService

router = APIRouter(prefix="/mes-quality", tags=["MES Quality"])
service = MesQualityService()


@router.get("/status")
def status(_: User = Depends(get_current_user)):
    return service.status()


@router.post("/simulate-result")
def simulate_result(payload: MesQualityResultCreate, db: Session = Depends(get_db), actor: User = Depends(require_roles("SUPERVISOR", "ADMIN"))):
    item = service.record(db, payload, actor.username)
    write_audit(db, "MES_QUALITY_RESULT_SIMULATED", actor, "MES_QUALITY_RESULT", item.id, {"serial": item.serial_number, "result": item.result, "line_stopped": False})
    return {"id": item.id, "serial_number": item.serial_number, "result": item.result, "attempt_number": item.attempt_number, "tested_at": item.tested_at}


@router.get("/incidents")
def incidents(status: str | None = Query(default="PENDING_REMOVAL"), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.list_incidents(db, status)


@router.post("/incidents/{incident_id}/confirm-removal")
def confirm_removal(incident_id: int, payload: RemovalConfirmation, db: Session = Depends(get_db), actor: User = Depends(require_roles("SUPERVISOR", "ADMIN"))):
    item = service.confirm_removal(db, incident_id, actor.username, payload.note)
    write_audit(db, "MES_NG_REMOVAL_CONFIRMED", actor, "PALLET_QUALITY_INCIDENT", item.id, {"pallet_id": item.pallet_id, "position": item.pallet_position, "note": item.resolution_note})
    return {"id": item.id, "status": item.status, "resolved_at": item.resolved_at, "resolved_by_username": item.resolved_by_username}
