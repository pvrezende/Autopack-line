from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.pallet_config import PalletConfig
from app.models.production_line import ProductionLine
from app.models.production_target import ProductionTarget
from app.models.indicator_threshold import IndicatorThreshold
from app.repositories.production_repository import ProductionRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.pallet_config import PalletConfigUpsert
from app.schemas.production_line import ProductionLineCreate
from app.schemas.production_target import ProductionTargetUpsert
from app.schemas.indicator_threshold import IndicatorThresholdUpsert


class ConfigurationService:
    def __init__(self) -> None:
        self.repository = ProductionRepository()
        self.products = ProductRepository()

    def list_lines(self, db: Session) -> list[ProductionLine]:
        return self.repository.list_lines(db)

    def create_line(self, db: Session, payload: ProductionLineCreate) -> ProductionLine:
        line = ProductionLine(**payload.model_dump())
        try:
            return self.repository.create_line(db, line)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código da linha já cadastrado") from exc

    def list_pallet_configs(self, db: Session) -> list[PalletConfig]:
        return self.repository.list_pallet_configs(db)

    def set_pallet_config(self, db: Session, payload: PalletConfigUpsert) -> PalletConfig:
        if not self.products.get(db, payload.product_id):
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        if not self.repository.get_line(db, payload.line_id):
            raise HTTPException(status_code=404, detail="Linha não encontrada")
        now = datetime.utcnow()
        self.repository.close_active_pallet_config(db, payload.product_id, payload.line_id, now)
        config = PalletConfig(
            product_id=payload.product_id,
            line_id=payload.line_id,
            max_boxes=payload.max_boxes,
            active=True,
            valid_from=now,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config

    def list_targets(self, db: Session) -> list[ProductionTarget]:
        return self.repository.list_targets(db)

    def set_target(self, db: Session, payload: ProductionTargetUpsert) -> ProductionTarget:
        if payload.hourly_target is None and payload.daily_target is None and payload.takt_seconds is None:
            raise HTTPException(status_code=422, detail="Informe pelo menos uma meta: meta/hora, meta diária ou takt")
        if not self.repository.get_line(db, payload.line_id):
            raise HTTPException(status_code=404, detail="Linha não encontrada")
        if payload.product_id is not None and not self.products.get(db, payload.product_id):
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        now = datetime.utcnow()
        current = self.repository.get_active_target(db, payload.line_id, payload.product_id)
        if current:
            current.active = False
            current.valid_until = now
        target = ProductionTarget(
            **payload.model_dump(),
            active=True,
            valid_from=now,
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        return target

    def list_indicator_thresholds(self, db: Session) -> list[IndicatorThreshold]:
        return self.repository.list_indicator_thresholds(db)

    def set_indicator_threshold(self, db: Session, payload: IndicatorThresholdUpsert) -> IndicatorThreshold:
        if not self.repository.get_line(db, payload.line_id):
            raise HTTPException(status_code=404, detail="Linha não encontrada")
        if payload.product_id is not None and not self.products.get(db, payload.product_id):
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        now = datetime.utcnow()
        current = self.repository.get_active_indicator_threshold(db, payload.line_id, payload.product_id)
        if current:
            current.active = False
            current.valid_until = now
        item = IndicatorThreshold(**payload.model_dump(), active=True, valid_from=now)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
