from datetime import datetime, time, timezone
from math import ceil
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.downtime_event import DowntimeEvent
from app.models.planned_break import PlannedBreak
from app.models.production_order import ProductionOrder
from app.models.user import User
from app.models.work_shift import WorkShift
from app.repositories.production_repository import ProductionRepository
from app.schemas.work_schedule import DowntimeCreate, PlannedBreakCreate, PlannedBreakUpdate, WorkShiftCreate, WorkShiftUpdate
from app.services.audit_service import write_audit


def _minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _period_minutes(start: time, end: time) -> int:
    start_m = _minutes(start); end_m = _minutes(end)
    return end_m - start_m if end_m > start_m else 24 * 60 - start_m + end_m


def _crosses_midnight(start: time, end: time) -> bool:
    return _minutes(end) <= _minutes(start)


def _utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


class WorkScheduleService:
    def __init__(self) -> None:
        self.repository = ProductionRepository()

    def _shift_dict(self, db: Session, shift: WorkShift) -> dict:
        line = self.repository.get_line(db, shift.line_id)
        breaks = db.scalars(select(PlannedBreak).where(PlannedBreak.shift_id == shift.id, PlannedBreak.active.is_(True))).all()
        # Time puro é proposital: horários do turno são parâmetros locais, não timestamps UTC.
        break_minutes = sum(_period_minutes(item.start_time, item.end_time) for item in breaks)
        total = _period_minutes(shift.start_time, shift.end_time)
        return {
            "id": shift.id, "line_id": shift.line_id, "line_code": line.code if line else None,
            "code": shift.code, "name": shift.name, "start_time": shift.start_time, "end_time": shift.end_time,
            "crosses_midnight": shift.crosses_midnight, "active": shift.active,
            "planned_minutes": total, "planned_break_minutes": break_minutes,
            "net_planned_minutes": max(0, total - break_minutes),
        }

    def list_shifts(self, db: Session, *, page: int, page_size: int, line_id: int | None, active: bool | None) -> dict:
        stmt = select(WorkShift); count_stmt = select(func.count()).select_from(WorkShift)
        if line_id:
            stmt = stmt.where(WorkShift.line_id == line_id); count_stmt = count_stmt.where(WorkShift.line_id == line_id)
        if active is not None:
            stmt = stmt.where(WorkShift.active.is_(active)); count_stmt = count_stmt.where(WorkShift.active.is_(active))
        total = int(db.scalar(count_stmt) or 0)
        items = db.scalars(stmt.order_by(WorkShift.line_id, WorkShift.start_time).offset((page - 1) * page_size).limit(page_size)).all()
        return {"items": [self._shift_dict(db, x) for x in items], "total": total, "page": page, "page_size": page_size, "total_pages": max(1, ceil(total / page_size))}

    def create_shift(self, db: Session, payload: WorkShiftCreate, actor: User) -> dict:
        if payload.start_time == payload.end_time:
            raise HTTPException(422, "Início e fim do turno não podem ser iguais")
        if not self.repository.get_line(db, payload.line_id):
            raise HTTPException(404, "Linha não encontrada")
        item = WorkShift(**payload.model_dump(), crosses_midnight=_crosses_midnight(payload.start_time, payload.end_time))
        try:
            db.add(item); db.flush()
            write_audit(db, "Turno criado", actor, "WORK_SHIFT", item.id, {"line_id": item.line_id, "code": item.code}, commit=False)
            db.commit(); db.refresh(item)
            return self._shift_dict(db, item)
        except IntegrityError as exc:
            db.rollback(); raise HTTPException(409, "Já existe um turno com esse código para a linha") from exc

    def update_shift(self, db: Session, shift_id: int, payload: WorkShiftUpdate, actor: User) -> dict:
        item = db.get(WorkShift, shift_id)
        if not item: raise HTTPException(404, "Turno não encontrado")
        data = payload.model_dump(exclude_unset=True)
        start = data.get("start_time", item.start_time); end = data.get("end_time", item.end_time)
        if start == end: raise HTTPException(422, "Início e fim do turno não podem ser iguais")
        for key, value in data.items(): setattr(item, key, value)
        item.crosses_midnight = _crosses_midnight(start, end)
        write_audit(db, "Turno editado", actor, "WORK_SHIFT", item.id, data, commit=False)
        db.commit(); db.refresh(item); return self._shift_dict(db, item)

    def _break_dict(self, db: Session, item: PlannedBreak) -> dict:
        shift = db.get(WorkShift, item.shift_id); line = self.repository.get_line(db, shift.line_id) if shift else None
        return {"id": item.id, "shift_id": item.shift_id, "shift_code": shift.code if shift else None, "shift_name": shift.name if shift else None,
                "line_id": shift.line_id if shift else None, "line_code": line.code if line else None, "name": item.name,
                "break_type": item.break_type, "start_time": item.start_time, "end_time": item.end_time,
                "duration_minutes": _period_minutes(item.start_time, item.end_time), "active": item.active}

    def _validate_break(self, db: Session, shift_id: int, start: time, end: time) -> WorkShift:
        shift = db.get(WorkShift, shift_id)
        if not shift: raise HTTPException(404, "Turno não encontrado")
        if start == end: raise HTTPException(422, "Início e fim da pausa não podem ser iguais")
        duration = _period_minutes(start, end)
        if duration >= _period_minutes(shift.start_time, shift.end_time):
            raise HTTPException(422, "A pausa deve ser menor que a duração do turno")
        # Normaliza os horários como deslocamento a partir do início do turno.
        base = _minutes(shift.start_time)
        def offset(t: time) -> int:
            value = _minutes(t) - base
            return value if value >= 0 else value + 24 * 60
        s = offset(start); e = offset(end)
        if e <= s: e += 24 * 60
        if s < 0 or e > _period_minutes(shift.start_time, shift.end_time):
            raise HTTPException(422, "A pausa precisa estar dentro do horário do turno")
        return shift

    def _ensure_no_break_overlap(self, db: Session, shift: WorkShift, start: time, end: time, ignore_id: int | None = None) -> None:
        base = _minutes(shift.start_time)
        def interval(a: time, b: time) -> tuple[int, int]:
            x = _minutes(a) - base; y = _minutes(b) - base
            if x < 0: x += 24 * 60
            if y < 0: y += 24 * 60
            if y <= x: y += 24 * 60
            return x, y
        start_i, end_i = interval(start, end)
        stmt = select(PlannedBreak).where(PlannedBreak.shift_id == shift.id, PlannedBreak.active.is_(True))
        if ignore_id is not None: stmt = stmt.where(PlannedBreak.id != ignore_id)
        for current in db.scalars(stmt).all():
            current_start, current_end = interval(current.start_time, current.end_time)
            if max(start_i, current_start) < min(end_i, current_end):
                raise HTTPException(409, f"A pausa conflita com '{current.name}' ({current.start_time.strftime('%H:%M')}–{current.end_time.strftime('%H:%M')})")

    def list_breaks(self, db: Session, *, page: int, page_size: int, shift_id: int | None, active: bool | None) -> dict:
        stmt = select(PlannedBreak); count_stmt = select(func.count()).select_from(PlannedBreak)
        if shift_id:
            stmt = stmt.where(PlannedBreak.shift_id == shift_id); count_stmt = count_stmt.where(PlannedBreak.shift_id == shift_id)
        if active is not None:
            stmt = stmt.where(PlannedBreak.active.is_(active)); count_stmt = count_stmt.where(PlannedBreak.active.is_(active))
        total = int(db.scalar(count_stmt) or 0)
        items = db.scalars(stmt.order_by(PlannedBreak.shift_id, PlannedBreak.start_time).offset((page - 1) * page_size).limit(page_size)).all()
        return {"items": [self._break_dict(db, x) for x in items], "total": total, "page": page, "page_size": page_size, "total_pages": max(1, ceil(total / page_size))}

    def create_break(self, db: Session, payload: PlannedBreakCreate, actor: User) -> dict:
        shift = self._validate_break(db, payload.shift_id, payload.start_time, payload.end_time)
        if payload.active: self._ensure_no_break_overlap(db, shift, payload.start_time, payload.end_time)
        item = PlannedBreak(**payload.model_dump()); db.add(item); db.flush()
        write_audit(db, "Pausa planejada criada", actor, "PLANNED_BREAK", item.id, {"shift_id": item.shift_id, "type": item.break_type}, commit=False)
        db.commit(); db.refresh(item); return self._break_dict(db, item)

    def update_break(self, db: Session, break_id: int, payload: PlannedBreakUpdate, actor: User) -> dict:
        item = db.get(PlannedBreak, break_id)
        if not item: raise HTTPException(404, "Pausa não encontrada")
        data = payload.model_dump(exclude_unset=True); start = data.get("start_time", item.start_time); end = data.get("end_time", item.end_time)
        shift = self._validate_break(db, item.shift_id, start, end)
        will_be_active = data.get("active", item.active)
        if will_be_active: self._ensure_no_break_overlap(db, shift, start, end, ignore_id=item.id)
        for key, value in data.items(): setattr(item, key, value)
        write_audit(db, "Pausa planejada editada", actor, "PLANNED_BREAK", item.id, data, commit=False)
        db.commit(); db.refresh(item); return self._break_dict(db, item)

    def _downtime_dict(self, db: Session, item: DowntimeEvent) -> dict:
        line = self.repository.get_line(db, item.line_id); order = db.get(ProductionOrder, item.production_order_id) if item.production_order_id else None; shift = db.get(WorkShift, item.shift_id) if item.shift_id else None
        end = item.ended_at or datetime.utcnow(); duration = max(0, int((end - item.started_at).total_seconds() // 60))
        return {"id": item.id, "line_id": item.line_id, "line_code": line.code if line else None,
                "production_order_id": item.production_order_id, "production_order": order.order_number if order else None,
                "shift_id": item.shift_id, "shift_code": shift.code if shift else None, "category": item.category, "reason": item.reason,
                "status": item.status, "started_at": item.started_at, "ended_at": item.ended_at, "duration_minutes": duration,
                "notes": item.notes, "created_by_username": item.created_by_username, "closed_by_username": item.closed_by_username}

    def list_downtimes(self, db: Session, *, page: int, page_size: int, line_id: int | None, status: str | None, category: str | None) -> dict:
        stmt = select(DowntimeEvent); count_stmt = select(func.count()).select_from(DowntimeEvent)
        for condition in ([DowntimeEvent.line_id == line_id] if line_id else []): stmt = stmt.where(condition); count_stmt = count_stmt.where(condition)
        if status: stmt = stmt.where(DowntimeEvent.status == status); count_stmt = count_stmt.where(DowntimeEvent.status == status)
        if category: stmt = stmt.where(DowntimeEvent.category == category); count_stmt = count_stmt.where(DowntimeEvent.category == category)
        total = int(db.scalar(count_stmt) or 0)
        items = db.scalars(stmt.order_by(DowntimeEvent.started_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
        return {"items": [self._downtime_dict(db, x) for x in items], "total": total, "page": page, "page_size": page_size, "total_pages": max(1, ceil(total / page_size))}

    def create_downtime(self, db: Session, payload: DowntimeCreate, actor: User) -> dict:
        if not self.repository.get_line(db, payload.line_id): raise HTTPException(404, "Linha não encontrada")
        if payload.production_order_id:
            order = db.get(ProductionOrder, payload.production_order_id)
            if not order: raise HTTPException(404, "OP não encontrada")
            if order.line_id and order.line_id != payload.line_id: raise HTTPException(422, "A OP pertence a outra linha")
        if payload.shift_id:
            shift = db.get(WorkShift, payload.shift_id)
            if not shift: raise HTTPException(404, "Turno não encontrado")
            if shift.line_id != payload.line_id: raise HTTPException(422, "O turno pertence a outra linha")
        started = _utc_naive(payload.started_at); ended = _utc_naive(payload.ended_at) if payload.ended_at else None
        if ended and ended <= started: raise HTTPException(422, "O fim da parada deve ser posterior ao início")
        item = DowntimeEvent(line_id=payload.line_id, production_order_id=payload.production_order_id, shift_id=payload.shift_id,
                             category=payload.category, reason=payload.reason, status="CLOSED" if ended else "OPEN",
                             started_at=started, ended_at=ended, notes=payload.notes, created_by_username=actor.username,
                             closed_by_username=actor.username if ended else None)
        db.add(item); db.flush(); write_audit(db, "Parada registrada", actor, "DOWNTIME", item.id, {"category": item.category, "reason": item.reason}, commit=False)
        db.commit(); db.refresh(item); return self._downtime_dict(db, item)

    def close_downtime(self, db: Session, event_id: int, ended_at: datetime, actor: User) -> dict:
        item = db.get(DowntimeEvent, event_id)
        if not item: raise HTTPException(404, "Parada não encontrada")
        if item.status == "CLOSED": raise HTTPException(409, "Parada já encerrada")
        ended = _utc_naive(ended_at)
        if ended <= item.started_at: raise HTTPException(422, "O fim da parada deve ser posterior ao início")
        item.ended_at = ended; item.status = "CLOSED"; item.closed_by_username = actor.username
        write_audit(db, "Parada encerrada", actor, "DOWNTIME", item.id, {"duration_minutes": int((ended-item.started_at).total_seconds()//60)}, commit=False)
        db.commit(); db.refresh(item); return self._downtime_dict(db, item)

    def summary(self, db: Session) -> dict:
        return {
            "active_shifts": int(db.scalar(select(func.count()).select_from(WorkShift).where(WorkShift.active.is_(True))) or 0),
            "active_planned_breaks": int(db.scalar(select(func.count()).select_from(PlannedBreak).where(PlannedBreak.active.is_(True))) or 0),
            "open_downtimes": int(db.scalar(select(func.count()).select_from(DowntimeEvent).where(DowntimeEvent.status == "OPEN")) or 0),
        }
