from datetime import datetime
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models import Pallet, PalletItem, Product, ProductionLine, ProductionOrder, ProductionUnit
from app.services.mes_quality_service import MesQualityService


def test_late_ng_creates_persistent_pallet_position_alert(monkeypatch):
    monkeypatch.setattr("app.services.mes_quality_service.settings.mes_quality_simulator_enabled", True)
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([
            Product(id=1, sku="SKU-1", ean="7908412552656", model="HJFE12C2CG", name="Produto"),
            ProductionLine(id=1, code="L01", name="Linha 1"),
            ProductionOrder(id=1, order_number="OP-1", product_id=1, line_id=1),
            ProductionUnit(id=1, serial_number="NG-LATE-001", product_id=1, production_order_id=1, status="PALLETIZED"),
            Pallet(id=1, pallet_code="PAL-001", line_id=1, product_id=1, production_order_id=1, target_quantity=3, current_quantity=3, status="FULL"),
            PalletItem(id=1, pallet_id=1, production_unit_id=1, sequence_number=3, position=3),
        ])
        db.commit()
        MesQualityService().record(db, SimpleNamespace(
            serial_number="NG-LATE-001", result="NG", external_event_id="MES-1",
            tested_at=datetime.utcnow(), raw_payload={"result": "NG"},
        ), "supervisor")
        incidents = MesQualityService().list_incidents(db)
        assert len(incidents) == 1
        assert incidents[0]["pallet_code"] == "PAL-001"
        assert incidents[0]["pallet_position"] == 3
        assert db.get(Pallet, 1).quality_status == "HOLD_NG"
        MesQualityService().confirm_removal(db, incidents[0]["id"], "supervisor", "Unidade retirada e segregada")
        assert MesQualityService().list_incidents(db) == []
        assert db.get(Pallet, 1).quality_status == "CLEAR"
