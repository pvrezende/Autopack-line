from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.mes_quality_result import MesQualityResult
from app.models.pallet import Pallet
from app.models.pallet_item import PalletItem
from app.models.pallet_quality_incident import PalletQualityIncident
from app.models.production_order import ProductionOrder
from app.models.production_unit import ProductionUnit
from app.models.product import Product


class MesQualityService:
    def status(self) -> dict:
        return {
            "enabled": settings.mes_quality_enabled,
            "simulator_enabled": settings.mes_quality_simulator_enabled,
            "mode": settings.mes_quality_mode,
            "endpoint_configured": bool(settings.mes_quality_base_url),
            "line_stops_on_ng": False,
            "message": (
                "Contrato real do MES Elgin pendente. O simulador permite validar OK/NG, "
                "alerta persistente, palete, posição e retirada sem parar a linha."
            ),
        }

    def record(self, db: Session, payload, username: str) -> MesQualityResult:
        if not settings.mes_quality_simulator_enabled:
            raise HTTPException(status_code=409, detail="Simulador de qualidade MES desabilitado")
        serial = payload.serial_number.strip()
        unit = db.scalar(select(ProductionUnit).where(ProductionUnit.serial_number == serial))
        if payload.external_event_id:
            existing = db.scalar(select(MesQualityResult).where(MesQualityResult.external_event_id == payload.external_event_id))
            if existing:
                return existing
        attempt = int(db.scalar(select(func.count(MesQualityResult.id)).where(MesQualityResult.serial_number == serial)) or 0) + 1
        item = MesQualityResult(
            serial_number=serial,
            production_unit_id=unit.id if unit else None,
            result=payload.result,
            source="SIMULATOR",
            external_event_id=payload.external_event_id,
            attempt_number=attempt,
            tested_at=payload.tested_at or datetime.utcnow(),
            raw_payload=payload.raw_payload,
            created_by_username=username,
        )
        db.add(item)
        db.flush()
        # O retorno do MES pode chegar antes ou depois da deposição. Se a unidade
        # já estiver no palete, o alerta deve nascer imediatamente e sem parar a linha.
        if unit:
            pallet_item = db.scalar(select(PalletItem).where(PalletItem.production_unit_id == unit.id))
            if pallet_item:
                pallet = db.get(Pallet, pallet_item.pallet_id)
                if pallet:
                    self.register_placement(db, unit, pallet, pallet_item)
        db.commit()
        db.refresh(item)
        return item

    def register_placement(self, db: Session, unit: ProductionUnit, pallet: Pallet, pallet_item: PalletItem) -> None:
        quality = db.scalar(
            select(MesQualityResult)
            .where(MesQualityResult.serial_number == unit.serial_number)
            .order_by(MesQualityResult.tested_at.desc(), MesQualityResult.id.desc())
            .limit(1)
        )
        if not quality:
            return
        if quality.production_unit_id is None:
            quality.production_unit_id = unit.id
        if quality.result != "NG":
            return
        db.flush()
        existing = db.scalar(select(PalletQualityIncident).where(PalletQualityIncident.quality_result_id == quality.id))
        if existing:
            return
        db.add(PalletQualityIncident(
            quality_result_id=quality.id,
            production_unit_id=unit.id,
            pallet_id=pallet.id,
            pallet_item_id=pallet_item.id,
            pallet_position=pallet_item.position or pallet_item.sequence_number,
            status="PENDING_REMOVAL",
        ))
        pallet.quality_status = "HOLD_NG"

    def list_incidents(self, db: Session, status: str | None = "PENDING_REMOVAL") -> list[dict]:
        query = (
            select(PalletQualityIncident, MesQualityResult, ProductionUnit, Pallet, Product, ProductionOrder)
            .join(MesQualityResult, MesQualityResult.id == PalletQualityIncident.quality_result_id)
            .join(ProductionUnit, ProductionUnit.id == PalletQualityIncident.production_unit_id)
            .join(Pallet, Pallet.id == PalletQualityIncident.pallet_id)
            .join(Product, Product.id == ProductionUnit.product_id)
            .join(ProductionOrder, ProductionOrder.id == ProductionUnit.production_order_id)
            .order_by(PalletQualityIncident.id.desc())
        )
        if status:
            query = query.where(PalletQualityIncident.status == status)
        return [{
            "id": incident.id,
            "status": incident.status,
            "serial_number": unit.serial_number,
            "result": quality.result,
            "source": quality.source,
            "tested_at": quality.tested_at,
            "pallet_id": pallet.id,
            "pallet_code": pallet.pallet_code,
            "pallet_position": incident.pallet_position,
            "product_model": product.model,
            "production_order": order.order_number,
            "detected_at": incident.detected_at,
            "resolved_at": incident.resolved_at,
            "resolved_by_username": incident.resolved_by_username,
            "resolution_note": incident.resolution_note,
        } for incident, quality, unit, pallet, product, order in db.execute(query)]

    def confirm_removal(self, db: Session, incident_id: int, username: str, note: str) -> PalletQualityIncident:
        incident = db.get(PalletQualityIncident, incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Alerta NG não encontrado")
        if incident.status == "REMOVED":
            return incident
        incident.status = "REMOVED"
        incident.resolved_at = datetime.utcnow()
        incident.resolved_by_username = username
        incident.resolution_note = note.strip()
        pending = db.scalar(select(func.count(PalletQualityIncident.id)).where(
            PalletQualityIncident.pallet_id == incident.pallet_id,
            PalletQualityIncident.status == "PENDING_REMOVAL",
            PalletQualityIncident.id != incident.id,
        )) or 0
        if not pending:
            pallet = db.get(Pallet, incident.pallet_id)
            if pallet:
                pallet.quality_status = "CLEAR"
        db.commit()
        db.refresh(incident)
        return incident
