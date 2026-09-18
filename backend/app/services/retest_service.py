from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.production_unit import ProductionUnit
from app.models.product import Product
from app.models.production_order import ProductionOrder
from app.models.retest_attempt import RetestAttempt
from app.models.rework_order import ReworkOrder
from app.schemas.retest import RetestSimulationRequest


class RetestService:
    def diagnostic_status(self) -> dict:
        return {
            "stage": "7.32",
            "real_retest_enabled": settings.retest_enabled,
            "simulator_enabled": settings.retest_simulator_enabled,
            "physical_plc_required": False,
            "max_attempts": settings.retest_max_attempts,
            "mode": "OFFLINE_FOUNDATION" if not settings.retest_enabled else "REAL_RULES_ENABLED",
            "safety_rules": [
                "O simulador nunca altera contadores, paletes ou o estado produtivo da unidade.",
                "Fontes MES, CLP e OPERATOR permanecem bloqueadas enquanto RETEST_ENABLED=false.",
                "A mesma chave de idempotencia retorna a tentativa existente.",
                "Uma aprovacao simulada exige rejeicao anterior e autorizacao explicita no teste.",
            ],
            "pending_definitions": [
                "Origem oficial da aprovacao e reprovacao.",
                "Aprovação nominal dos autorizadores por Processo/Qualidade.",
                "Contrato e disponibilidade do MES.",
                "Impacto definitivo em producao e paletizacao.",
            ],
            "message": "Consulta e historico de reteste consolidados offline; execucao real continua bloqueada.",
        }

    def search_units(self, db: Session, query: str | None = None, limit: int = 20) -> list[dict]:
        attempt_count = (
            select(func.count(RetestAttempt.id))
            .where(RetestAttempt.production_unit_id == ProductionUnit.id)
            .correlate(ProductionUnit)
            .scalar_subquery()
        )
        last_decision = (
            select(RetestAttempt.decision)
            .where(RetestAttempt.production_unit_id == ProductionUnit.id)
            .order_by(RetestAttempt.attempt_number.desc())
            .limit(1)
            .correlate(ProductionUnit)
            .scalar_subquery()
        )
        statement = (
            select(
                ProductionUnit.id,
                ProductionUnit.serial_number,
                ProductionUnit.status.label("unit_status"),
                ProductionUnit.product_id,
                Product.model.label("product_model"),
                Product.name.label("product_name"),
                ProductionUnit.production_order_id,
                ProductionOrder.order_number.label("production_order"),
                attempt_count.label("attempt_count"),
                last_decision.label("last_decision"),
                ProductionUnit.created_at,
            )
            .join(Product, Product.id == ProductionUnit.product_id)
            .join(ProductionOrder, ProductionOrder.id == ProductionUnit.production_order_id)
            .order_by(ProductionUnit.id.desc())
            .limit(limit)
        )
        normalized = (query or "").strip()
        if normalized:
            like = f"%{normalized}%"
            statement = statement.where(or_(
                ProductionUnit.serial_number.like(like),
                Product.model.like(like),
                ProductionOrder.order_number.like(like),
            ))
        return [dict(row._mapping) for row in db.execute(statement)]

    def list_for_serial(self, db: Session, serial_number: str) -> list[RetestAttempt]:
        unit = db.scalar(select(ProductionUnit).where(ProductionUnit.serial_number == serial_number.strip()))
        if not unit:
            raise HTTPException(status_code=404, detail="Unidade não encontrada para o serial informado")
        return list(db.scalars(
            select(RetestAttempt)
            .where(RetestAttempt.production_unit_id == unit.id)
            .order_by(RetestAttempt.attempt_number.asc())
        ))

    def simulate(self, db: Session, payload: RetestSimulationRequest, username: str) -> tuple[RetestAttempt, bool]:
        if not settings.retest_simulator_enabled:
            raise HTTPException(status_code=409, detail="Simulador de reteste desabilitado")

        replay = db.scalar(select(RetestAttempt).where(RetestAttempt.idempotency_key == payload.idempotency_key))
        if replay:
            replay_unit = db.get(ProductionUnit, replay.production_unit_id)
            if not replay_unit or replay_unit.serial_number != payload.serial_number.strip() or replay.decision != payload.decision:
                raise HTTPException(status_code=409, detail="Chave de idempotência já utilizada por outra operação")
            return replay, True

        unit = db.scalar(select(ProductionUnit).where(ProductionUnit.serial_number == payload.serial_number.strip()))
        if not unit:
            raise HTTPException(status_code=404, detail="Unidade não encontrada para o serial informado")
        if unit.status == "PALLETIZED":
            raise HTTPException(status_code=409, detail="Unidade já depositada não pode entrar em reteste; abra uma ordem de retrabalho.")
        if not (payload.reason_text or "").strip():
            raise HTTPException(status_code=422, detail="Motivo do reteste/reprovação é obrigatório")

        prior_rejected = db.scalar(
            select(RetestAttempt.id)
            .where(RetestAttempt.production_unit_id == unit.id, RetestAttempt.decision == "REJECTED")
            .limit(1)
        )
        if payload.decision == "APPROVED" and (not prior_rejected or not payload.authorized_for_retest):
            raise HTTPException(
                status_code=409,
                detail="Aprovação simulada exige rejeição anterior e autorização explícita de reteste",
            )

        next_attempt = int(db.scalar(
            select(func.coalesce(func.max(RetestAttempt.attempt_number), 0))
            .where(RetestAttempt.production_unit_id == unit.id)
        ) or 0) + 1
        if next_attempt > settings.retest_max_attempts:
            raise HTTPException(status_code=409, detail=f"Limite configurado de {settings.retest_max_attempts} tentativas atingido")
        authorization = "SIMULATED_AUTHORIZED" if payload.authorized_for_retest else "PENDING_PROCESS_DEFINITION"
        attempt = RetestAttempt(
            production_unit_id=unit.id,
            attempt_number=next_attempt,
            decision=payload.decision,
            source="SIMULATOR",
            authorization_status=authorization,
            reason_code=payload.reason_code,
            reason_text=payload.reason_text,
            idempotency_key=payload.idempotency_key,
            counted_in_production=False,
            details={"stage": "7.32", "offline_only": True, "unit_status_preserved": unit.status},
            created_by_username=username,
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt, False

    def create_rework_order(self, db: Session, serial_number: str, reason: str, username: str) -> ReworkOrder:
        unit = db.scalar(select(ProductionUnit).where(ProductionUnit.serial_number == serial_number.strip()))
        if not unit:
            raise HTTPException(status_code=404, detail="Unidade não encontrada")
        if unit.status != "PALLETIZED":
            raise HTTPException(status_code=409, detail="Ordem de retrabalho é exclusiva para unidade já depositada")
        existing = db.scalar(select(ReworkOrder).where(
            ReworkOrder.original_production_unit_id == unit.id,
            ReworkOrder.status == "OPEN",
        ))
        if existing:
            return existing
        item = ReworkOrder(
            original_production_unit_id=unit.id,
            reason=reason.strip(),
            created_by_username=username,
            status="OPEN",
        )
        db.add(item); db.commit(); db.refresh(item)
        return item
