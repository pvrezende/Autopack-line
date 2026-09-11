from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.pallet_config import PalletConfigRead, PalletConfigUpsert
from app.schemas.production_line import ProductionLineCreate, ProductionLineRead
from app.schemas.production_target import ProductionTargetRead, ProductionTargetUpsert
from app.schemas.indicator_threshold import IndicatorThresholdRead, IndicatorThresholdUpsert
from app.services.configuration_service import ConfigurationService
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.services.audit_service import write_audit

router = APIRouter(tags=["Configurations"])
service = ConfigurationService()


@router.get("/lines", response_model=list[ProductionLineRead])
def list_lines(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.list_lines(db)


@router.post("/lines", response_model=ProductionLineRead, status_code=status.HTTP_201_CREATED)
def create_line(payload: ProductionLineCreate, db: Session = Depends(get_db), actor: User = Depends(require_roles("ADMIN"))):
    item = service.create_line(db, payload)
    write_audit(db, "LINE_CREATED", actor, "PRODUCTION_LINE", item.id, {"code": item.code})
    return item


@router.get("/pallet-configs", response_model=list[PalletConfigRead])
def list_pallet_configs(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.list_pallet_configs(db)


@router.post("/pallet-configs", response_model=PalletConfigRead, status_code=status.HTTP_201_CREATED)
def set_pallet_config(payload: PalletConfigUpsert, db: Session = Depends(get_db), actor: User = Depends(require_roles("ADMIN"))):
    item = service.set_pallet_config(db, payload)
    write_audit(db, "PALLET_CONFIG_CHANGED", actor, "PALLET_CONFIG", item.id, {"product_id": item.product_id, "line_id": item.line_id, "max_boxes": item.max_boxes})
    return item


@router.get("/production-targets", response_model=list[ProductionTargetRead])
def list_targets(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.list_targets(db)


@router.post("/production-targets", response_model=ProductionTargetRead, status_code=status.HTTP_201_CREATED)
def set_target(payload: ProductionTargetUpsert, db: Session = Depends(get_db), actor: User = Depends(require_roles("ADMIN"))):
    item = service.set_target(db, payload)
    write_audit(db, "PRODUCTION_TARGET_CHANGED", actor, "PRODUCTION_TARGET", item.id)
    return item


@router.get("/indicator-thresholds", response_model=list[IndicatorThresholdRead])
def list_indicator_thresholds(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.list_indicator_thresholds(db)


@router.post("/indicator-thresholds", response_model=IndicatorThresholdRead, status_code=status.HTTP_201_CREATED)
def set_indicator_threshold(payload: IndicatorThresholdUpsert, db: Session = Depends(get_db), actor: User = Depends(require_roles("ADMIN"))):
    item = service.set_indicator_threshold(db, payload)
    write_audit(db, "INDICATOR_THRESHOLD_CHANGED", actor, "INDICATOR_THRESHOLD", item.id, {"line_id": item.line_id, "product_id": item.product_id})
    return item
