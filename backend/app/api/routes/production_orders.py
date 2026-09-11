from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.production_order import ProductionOrderCreate, ProductionOrderPage, ProductionOrderRead, ProductionOrderUpdate
from app.services.production_order_service import ProductionOrderService
from app.core.security import get_current_user, require_roles
from app.models.user import User

router = APIRouter(prefix="/production-orders", tags=["Production Orders"])
service = ProductionOrderService()


@router.get("", response_model=ProductionOrderPage)
def list_orders(
    page: int = Query(1, ge=1), page_size: int = Query(8, ge=4, le=50), status_filter: str | None = Query(None, alias="status"),
    line_id: int | None = Query(None, gt=0), product_id: int | None = Query(None, gt=0), search: str | None = None,
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    return service.list_page(db, page=page, page_size=page_size, status_filter=status_filter, line_id=line_id, product_id=product_id, search=search)


@router.get("/{order_id}", response_model=ProductionOrderRead)
def get_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.get(db, order_id)


@router.post("", response_model=ProductionOrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: ProductionOrderCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    return service.create(db, payload, user)


@router.put("/{order_id}", response_model=ProductionOrderRead)
def update_order(order_id: int, payload: ProductionOrderUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    return service.update(db, order_id, payload, user)


@router.post("/{order_id}/start", response_model=ProductionOrderRead)
def start_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("SUPERVISOR", "ADMIN"))):
    return service.transition(db, order_id, "start", user)


@router.post("/{order_id}/pause", response_model=ProductionOrderRead)
def pause_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("SUPERVISOR", "ADMIN"))):
    return service.transition(db, order_id, "pause", user)


@router.post("/{order_id}/finish", response_model=ProductionOrderRead)
def finish_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("SUPERVISOR", "ADMIN"))):
    return service.transition(db, order_id, "finish", user)


@router.post("/{order_id}/cancel", response_model=ProductionOrderRead)
def cancel_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    return service.transition(db, order_id, "cancel", user)
