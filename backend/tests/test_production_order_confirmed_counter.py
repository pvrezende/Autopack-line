from types import SimpleNamespace
from app.services.production_order_service import ProductionOrderService


class FakeRepository:
    def count_units_for_order(self, db, order_id):
        return 23

    def count_palletized_units_for_order(self, db, order_id):
        return 7

    def count_pallets_for_order(self, db, order_id, status):
        return 1 if status == "OPEN" else 2

    def get_line(self, db, line_id):
        return SimpleNamespace(code="L01", name="Linha 1")


class FakeProducts:
    def get(self, db, product_id):
        return SimpleNamespace(model="HJFE12C2CG", name="Produto")


def test_serialize_separates_valid_reads_from_confirmed_production():
    service = ProductionOrderService()
    service.repository = FakeRepository()
    service.products = FakeProducts()
    order = SimpleNamespace(
        id=10,
        order_number="000001275033",
        product_id=1,
        line_id=1,
        lot_code=None,
        planned_quantity=100,
        status="ACTIVE",
        source="LOCAL",
        notes=None,
        created_by_username=None,
        started_by_username=None,
        finished_by_username=None,
        started_at=None,
        finished_at=None,
        created_at=None,
        updated_at=None,
    )

    data = service._serialize(None, order)

    assert data["scanned_quantity"] == 23
    assert data["produced_quantity"] == 7
    assert data["progress_percent"] == 7.0
