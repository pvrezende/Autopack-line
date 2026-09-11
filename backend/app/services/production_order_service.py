from datetime import datetime
from math import ceil
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.production_order import ProductionOrder
from app.models.user import User
from app.repositories.production_repository import ProductionRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.production_order import ProductionOrderCreate, ProductionOrderUpdate
from app.services.audit_service import write_audit


class ProductionOrderService:
    def __init__(self) -> None:
        self.repository = ProductionRepository()
        self.products = ProductRepository()

    def _serialize(self, db: Session, order: ProductionOrder) -> dict:
        product = self.products.get(db, order.product_id)
        line = self.repository.get_line(db, order.line_id) if order.line_id else None
        scanned = self.repository.count_units_for_order(db, order.id)
        # "Produzido" representa saída confirmada pelo CLP/paletização, não apenas uma leitura VALID.
        produced = self.repository.count_palletized_units_for_order(db, order.id)
        open_pallets = self.repository.count_pallets_for_order(db, order.id, "OPEN")
        completed_pallets = self.repository.count_pallets_for_order(db, order.id, "FULL")
        planned = order.planned_quantity or 0
        return {
            "id": order.id,
            "order_number": order.order_number,
            "product_id": order.product_id,
            "product_model": product.model if product else None,
            "product_name": product.name if product else None,
            "line_id": order.line_id,
            "line_code": line.code if line else None,
            "line_name": line.name if line else None,
            "lot_code": order.lot_code,
            "planned_quantity": order.planned_quantity,
            "produced_quantity": produced,
            "scanned_quantity": scanned,
            "progress_percent": round(min(100, (produced / planned * 100)) if planned else 0, 1),
            "open_pallets": open_pallets,
            "completed_pallets": completed_pallets,
            "status": order.status,
            "source": order.source,
            "notes": order.notes,
            "created_by_username": order.created_by_username,
            "started_by_username": order.started_by_username,
            "finished_by_username": order.finished_by_username,
            "started_at": order.started_at,
            "finished_at": order.finished_at,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
        }

    def list_page(self, db: Session, *, page: int, page_size: int, status_filter: str | None, line_id: int | None, product_id: int | None, search: str | None) -> dict:
        items, total = self.repository.list_orders_page(
            db, page=page, page_size=page_size, status=status_filter, line_id=line_id, product_id=product_id, search=search,
        )
        return {
            "items": [self._serialize(db, item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, ceil(total / page_size)) if page_size else 1,
        }

    def get(self, db: Session, order_id: int) -> dict:
        order = self.repository.get_order(db, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="OP não encontrada")
        return self._serialize(db, order)

    def _validate_refs(self, db: Session, product_id: int, line_id: int | None) -> None:
        if not self.products.get(db, product_id):
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        if line_id and not self.repository.get_line(db, line_id):
            raise HTTPException(status_code=404, detail="Linha não encontrada")

    def create(self, db: Session, payload: ProductionOrderCreate, user: User) -> dict:
        self._validate_refs(db, payload.product_id, payload.line_id)
        order = ProductionOrder(
            **payload.model_dump(), status="OPEN", source="LOCAL", created_by_username=user.username,
        )
        try:
            db.add(order)
            db.flush()
            write_audit(db, "OP criada", user, "PRODUCTION_ORDER", order.id, {"order_number": order.order_number}, commit=False)
            db.commit(); db.refresh(order)
            return self._serialize(db, order)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="OP já cadastrada") from exc

    def update(self, db: Session, order_id: int, payload: ProductionOrderUpdate, user: User) -> dict:
        order = self.repository.get_order(db, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="OP não encontrada")
        if order.status in {"COMPLETED", "CANCELLED"}:
            raise HTTPException(status_code=409, detail="OP finalizada/cancelada não pode ser editada")
        data = payload.model_dump(exclude_unset=True)
        product_id = data.get("product_id", order.product_id)
        line_id = data.get("line_id", order.line_id)
        self._validate_refs(db, product_id, line_id)
        if self.repository.count_units_for_order(db, order.id) > 0 and product_id != order.product_id:
            raise HTTPException(status_code=409, detail="Não é possível trocar o produto de uma OP que já possui produção")
        for key, value in data.items():
            setattr(order, key, value)
        write_audit(db, "OP editada", user, "PRODUCTION_ORDER", order.id, data, commit=False)
        db.commit(); db.refresh(order)
        return self._serialize(db, order)

    def transition(self, db: Session, order_id: int, action: str, user: User) -> dict:
        order = self.repository.get_order(db, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="OP não encontrada")
        now = datetime.utcnow()
        if action == "start":
            if order.status not in {"OPEN", "PAUSED"}:
                raise HTTPException(status_code=409, detail="Somente OP aberta ou pausada pode ser iniciada")
            order.status = "ACTIVE"; order.started_at = order.started_at or now; order.started_by_username = user.username
            audit_action = "OP iniciada"
        elif action == "pause":
            if order.status != "ACTIVE": raise HTTPException(status_code=409, detail="Somente OP ativa pode ser pausada")
            order.status = "PAUSED"; audit_action = "OP pausada"
        elif action == "finish":
            if order.status not in {"ACTIVE", "PAUSED", "OPEN"}: raise HTTPException(status_code=409, detail="OP não pode ser finalizada neste estado")
            if self.repository.count_pallets_for_order(db, order.id, "OPEN") > 0:
                raise HTTPException(status_code=409, detail="Finalize o palete aberto antes de concluir a OP")
            order.status = "COMPLETED"; order.finished_at = now; order.finished_by_username = user.username
            audit_action = "OP finalizada"
        elif action == "cancel":
            if order.status == "COMPLETED": raise HTTPException(status_code=409, detail="OP concluída não pode ser cancelada")
            if self.repository.count_pallets_for_order(db, order.id, "OPEN") > 0:
                raise HTTPException(status_code=409, detail="Existe palete aberto vinculado à OP")
            order.status = "CANCELLED"; order.finished_at = now; order.finished_by_username = user.username
            audit_action = "OP cancelada"
        else:
            raise HTTPException(status_code=400, detail="Ação inválida")
        write_audit(db, audit_action, user, "PRODUCTION_ORDER", order.id, {"order_number": order.order_number}, commit=False)
        db.commit(); db.refresh(order)
        return self._serialize(db, order)
