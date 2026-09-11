from datetime import date, datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.dashboard import DashboardLossAnalysis, DashboardOEEHistory, DashboardOperational, DashboardSummary
from app.services.dashboard_service import DashboardService
from app.core.security import get_current_user, require_roles
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
service = DashboardService()


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.summary(db)


@router.get("/operational", response_model=DashboardOperational)
def operational(
    line_id: int | None = None,
    product_id: int | None = None,
    production_order: str | None = None,
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    return service.operational(
        db,
        line_id=line_id,
        product_id=product_id,
        production_order=production_order,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/oee-history", response_model=DashboardOEEHistory)
def oee_history(
    line_id: int = Query(..., ge=1),
    product_id: int | None = None,
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: Session = Depends(get_db), _: User = Depends(require_roles("SUPERVISOR", "ADMIN")),
):
    return service.oee_history(
        db, line_id=line_id, product_id=product_id, date_from=date_from, date_to=date_to
    )


@router.get("/loss-analysis", response_model=DashboardLossAnalysis)
def loss_analysis(
    line_id: int = Query(..., ge=1),
    product_id: int | None = None,
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: Session = Depends(get_db), _: User = Depends(require_roles("SUPERVISOR", "ADMIN")),
):
    return service.loss_analysis(
        db, line_id=line_id, product_id=product_id, date_from=date_from, date_to=date_to
    )
