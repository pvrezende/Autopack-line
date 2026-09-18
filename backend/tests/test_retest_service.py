from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.product import Product
from app.models.production_order import ProductionOrder
from app.models.production_unit import ProductionUnit
from app.models.retest_attempt import RetestAttempt
from app.schemas.retest import RetestSimulationRequest
from app.services.retest_service import RetestService


def seed_unit(db: Session) -> ProductionUnit:
    db.add(Product(id=1, sku="SKU", ean="789", model="MODEL", name="Produto", active=True))
    db.add(ProductionOrder(id=1, order_number="OP-1", product_id=1, status="ACTIVE", source="LOCAL"))
    unit = ProductionUnit(id=1, serial_number="SER-RETEST-1", product_id=1, production_order_id=1, status="SCANNED")
    db.add(unit)
    db.commit()
    return unit


def request(decision: str, key: str, authorized: bool = False) -> RetestSimulationRequest:
    return RetestSimulationRequest(
        serial_number="SER-RETEST-1",
        decision=decision,
        authorized_for_retest=authorized,
        reason_code="OFFLINE_TEST",
        reason_text="Cenário controlado",
        idempotency_key=key,
    )


def test_retest_rejection_then_authorized_approval_preserves_unit_state():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        unit = seed_unit(db)
        service = RetestService()
        rejected, replayed = service.simulate(db, request("REJECTED", "key-rejected"), "admin")
        approved, approved_replayed = service.simulate(db, request("APPROVED", "key-approved", True), "admin")

        assert replayed is False
        assert approved_replayed is False
        assert rejected.attempt_number == 1
        assert approved.attempt_number == 2
        assert approved.authorization_status == "SIMULATED_AUTHORIZED"
        assert approved.counted_in_production is False
        assert db.get(ProductionUnit, unit.id).status == "SCANNED"


def test_retest_idempotency_returns_same_attempt():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed_unit(db)
        service = RetestService()
        first, _ = service.simulate(db, request("REJECTED", "same-key"), "admin")
        replay, replayed = service.simulate(db, request("REJECTED", "same-key"), "admin")

        assert replayed is True
        assert replay.id == first.id
        assert len(list(db.scalars(select(RetestAttempt)))) == 1


def test_retest_approval_without_prior_rejection_is_blocked():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed_unit(db)
        service = RetestService()
        try:
            service.simulate(db, request("APPROVED", "approval-without-rejection", True), "admin")
            assert False, "A aprovação sem reprovação deveria ter sido bloqueada"
        except Exception as error:
            assert getattr(error, "status_code", None) == 409


def test_retest_idempotency_key_cannot_be_reused_for_other_decision():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed_unit(db)
        service = RetestService()
        service.simulate(db, request("REJECTED", "protected-key"), "admin")
        try:
            service.simulate(db, request("APPROVED", "protected-key", True), "admin")
            assert False, "A colisão de idempotência deveria ter sido bloqueada"
        except Exception as error:
            assert getattr(error, "status_code", None) == 409


def test_retest_status_keeps_real_flow_blocked_by_default():
    status = RetestService().diagnostic_status()
    assert status["stage"] == "7.32"
    assert status["real_retest_enabled"] is False
    assert status["simulator_enabled"] is True
    assert status["physical_plc_required"] is False


def test_retest_unit_search_returns_business_context_and_attempt_summary():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed_unit(db)
        service = RetestService()
        service.simulate(db, request("REJECTED", "search-key"), "admin")

        result = service.search_units(db, "SER-RETEST", 20)

        assert len(result) == 1
        assert result[0]["serial_number"] == "SER-RETEST-1"
        assert result[0]["product_model"] == "MODEL"
        assert result[0]["production_order"] == "OP-1"
        assert result[0]["attempt_count"] == 1
        assert result[0]["last_decision"] == "REJECTED"


def test_retest_unit_search_can_filter_by_order_and_model():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed_unit(db)
        service = RetestService()

        assert len(service.search_units(db, "OP-1", 20)) == 1
        assert len(service.search_units(db, "MODEL", 20)) == 1
        assert service.search_units(db, "NAO-EXISTE", 20) == []


def test_palletized_unit_is_blocked_from_retest_and_uses_rework_order():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        unit = seed_unit(db)
        unit.status = "PALLETIZED"; db.commit()
        service = RetestService()
        try:
            service.simulate(db, request("REJECTED", "palletized-key"), "admin")
            assert False, "Unidade depositada não pode entrar em reteste"
        except Exception as error:
            assert getattr(error, "status_code", None) == 409
        rework = service.create_rework_order(db, unit.serial_number, "Retrabalho autorizado", "admin")
        assert rework.original_production_unit_id == unit.id
        assert rework.status == "OPEN"
