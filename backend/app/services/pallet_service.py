from datetime import datetime
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.pallet import Pallet
from app.models.pallet_item import PalletItem
from app.repositories.production_repository import ProductionRepository
from app.schemas.pallet import PalletizeRequest, PalletizeResult


class PalletService:
    def __init__(self) -> None:
        self.repository = ProductionRepository()

    def list_page(self, db: Session, **filters):
        return self.repository.list_pallets_page(db, **filters)

    def palletize(self, db: Session, payload: PalletizeRequest) -> PalletizeResult:
        unit = self.repository.get_unit(db, payload.production_unit_id)
        if not unit:
            raise HTTPException(status_code=404, detail="Unidade não encontrada")
        if not self.repository.get_line(db, payload.line_id):
            raise HTTPException(status_code=404, detail="Linha não encontrada")
        if self.repository.get_pallet_item_by_unit(db, unit.id):
            raise HTTPException(status_code=409, detail="Unidade já foi paletizada")

        config = self.repository.get_active_pallet_config(db, unit.product_id, payload.line_id)
        if not config:
            raise HTTPException(
                status_code=422,
                detail="Configure a quantidade por palete para este produto e linha antes de paletizar",
            )

        try:
            pallet = self.repository.get_open_pallet_for_update(
                db, payload.line_id, unit.product_id, unit.production_order_id
            )
            if not pallet:
                pallet = Pallet(
                    pallet_code=f"PAL-{uuid4().hex[:12].upper()}",
                    line_id=payload.line_id,
                    product_id=unit.product_id,
                    production_order_id=unit.production_order_id,
                    target_quantity=config.max_boxes,
                    current_quantity=0,
                    status="OPEN",
                )
                db.add(pallet)
                db.flush()

            if pallet.current_quantity >= pallet.target_quantity:
                raise HTTPException(status_code=409, detail="Palete já atingiu a quantidade configurada")

            sequence = pallet.current_quantity + 1
            item = PalletItem(
                pallet_id=pallet.id,
                production_unit_id=unit.id,
                sequence_number=sequence,
                position=payload.position,
            )
            db.add(item)
            pallet.current_quantity = sequence
            unit.status = "PALLETIZED"
            completed_now = sequence >= pallet.target_quantity
            if completed_now:
                pallet.status = "FULL"
                pallet.completed_at = datetime.utcnow()

            db.commit()
            db.refresh(pallet)
            return PalletizeResult(
                pallet=pallet,
                production_unit_id=unit.id,
                sequence_number=sequence,
                completed_now=completed_now,
            )
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Conflito ao registrar paletização") from exc
