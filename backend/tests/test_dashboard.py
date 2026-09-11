from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database.base import Base
from app.models.product import Product
from app.models.production_line import ProductionLine
from app.models.production_order import ProductionOrder
from app.models.production_unit import ProductionUnit
from app.models.scan_event import ScanEvent
from app.models.pallet import Pallet
from app.models.pallet_item import PalletItem
from app.repositories.production_repository import ProductionRepository


def test_dashboard_operational_aggregates_real_data():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    now = datetime(2026, 8, 10, 12, 30, 0)
    with Session(engine) as db:
        product = Product(id=1, sku="HJFE12C2CG", ean="7908412552656", model="HJFE12C2CG", name="Condensadora", active=True)
        line = ProductionLine(id=1, code="L01", name="Linha 1", active=True)
        order = ProductionOrder(id=1, order_number="000001275033", product_id=1, status="OPEN", source="LOCAL")
        units = [
            ProductionUnit(id=1, serial_number="SER1", product_id=1, production_order_id=1, status="PALLETIZED"),
            ProductionUnit(id=2, serial_number="SER2", product_id=1, production_order_id=1, status="PALLETIZED"),
        ]
        scans = [
            ScanEvent(id=1, line_id=1, production_unit_id=1, raw_code="a", code_type="QR", serial_number="SER1", ean=product.ean, production_order=order.order_number, status="VALID", scanned_at=now),
            ScanEvent(id=2, line_id=1, production_unit_id=2, raw_code="b", code_type="QR", serial_number="SER2", ean=product.ean, production_order=order.order_number, status="VALID", scanned_at=now),
            ScanEvent(id=3, line_id=1, raw_code="bad", code_type="QR", status="INVALID", error_message="QR inválido", scanned_at=now),
        ]
        pallet = Pallet(id=1, pallet_code="PAL-1", line_id=1, product_id=1, production_order_id=1, target_quantity=3, current_quantity=2, status="OPEN", opened_at=now)
        items = [
            PalletItem(id=1, pallet_id=1, production_unit_id=1, sequence_number=1, added_at=now),
            PalletItem(id=2, pallet_id=1, production_unit_id=2, sequence_number=2, added_at=now),
        ]
        db.add_all([product, line, order, *units, *scans, pallet, *items])
        db.commit()
        result = ProductionRepository().dashboard_operational(db)
        assert result["summary"]["total_scans"] == 3
        assert result["summary"]["valid_scans"] == 2
        assert result["summary"]["invalid_scans"] == 1
        assert result["summary"]["palletized_units"] == 2
        assert result["summary"]["open_pallets"] == 1
        assert result["production_by_hour"] == [{"hour": "12:00", "quantity": 2}]
        assert result["open_pallets"][0]["progress_percent"] == 66.7
        assert result["recent_occurrences"][0]["status"] == "INVALID"
