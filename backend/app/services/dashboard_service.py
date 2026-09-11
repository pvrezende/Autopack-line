from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.repositories.production_repository import ProductionRepository
from app.models.downtime_event import DowntimeEvent
from app.models.planned_break import PlannedBreak
from app.models.work_shift import WorkShift
from app.models.scan_event import ScanEvent
from app.models.production_order import ProductionOrder
from app.models.product import Product
from app.schemas.dashboard import DashboardOperational, DashboardSummary


LOCAL_TZ = ZoneInfo("America/Manaus")


def _merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    valid = sorted((start, end) for start, end in intervals if end > start)
    if not valid:
        return []
    merged = [valid[0]]
    for start, end in valid[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _subtract_intervals(base: list[tuple[datetime, datetime]], cuts: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    result = _merge_intervals(base)
    for cut_start, cut_end in _merge_intervals(cuts):
        next_result: list[tuple[datetime, datetime]] = []
        for start, end in result:
            if cut_end <= start or cut_start >= end:
                next_result.append((start, end))
                continue
            if cut_start > start:
                next_result.append((start, min(cut_start, end)))
            if cut_end < end:
                next_result.append((max(cut_end, start), end))
        result = next_result
    return _merge_intervals(result)


def _intersections(base: list[tuple[datetime, datetime]], events: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    result: list[tuple[datetime, datetime]] = []
    for b_start, b_end in _merge_intervals(base):
        for e_start, e_end in _merge_intervals(events):
            start = max(b_start, e_start)
            end = min(b_end, e_end)
            if end > start:
                result.append((start, end))
    return _merge_intervals(result)


def _minutes(intervals: list[tuple[datetime, datetime]]) -> int:
    return int(round(sum((end - start).total_seconds() for start, end in _merge_intervals(intervals)) / 60))


class DashboardService:
    def __init__(self) -> None:
        self.repository = ProductionRepository()


    @staticmethod
    def _classify_indicator(metric: str, value: float | None, warning: float, critical: float) -> dict:
        if value is None:
            status = "NO_DATA"
        elif value < critical:
            status = "CRITICAL"
        elif value < warning:
            status = "WARNING"
        else:
            status = "OK"
        return {
            "metric": metric,
            "value": value,
            "warning_threshold": warning,
            "critical_threshold": critical,
            "status": status,
        }

    def _indicator_alerts(self, db: Session, *, line_id: int | None, product_id: int | None, oee: dict) -> dict:
        if line_id is None:
            return {"status": "SELECT_LINE", "source": None, "threshold_id": None, "overall_status": "NO_CONFIG"}
        threshold = None
        source = None
        if product_id is not None:
            threshold = self.repository.get_active_indicator_threshold(db, line_id, product_id)
            source = "PRODUCT" if threshold else None
        if threshold is None:
            threshold = self.repository.get_active_indicator_threshold(db, line_id, None)
            source = "LINE" if threshold else None
        if threshold is None:
            return {"status": "NO_CONFIG", "source": None, "threshold_id": None, "overall_status": "NO_CONFIG"}

        metrics = {
            "availability": self._classify_indicator("AVAILABILITY", oee.get("availability_percent"), float(threshold.availability_warning), float(threshold.availability_critical)),
            "performance": self._classify_indicator("PERFORMANCE", oee.get("performance_percent"), float(threshold.performance_warning), float(threshold.performance_critical)),
            "quality": self._classify_indicator("QUALITY", oee.get("quality_percent"), float(threshold.quality_warning), float(threshold.quality_critical)),
            "oee": self._classify_indicator("OEE", oee.get("oee_percent"), float(threshold.oee_warning), float(threshold.oee_critical)),
        }
        statuses = [item["status"] for item in metrics.values()]
        overall = "CRITICAL" if "CRITICAL" in statuses else "WARNING" if "WARNING" in statuses else "OK" if "OK" in statuses else "NO_DATA"
        return {
            "status": "OK",
            "source": source,
            "threshold_id": threshold.id,
            "overall_status": overall,
            **metrics,
        }

    def summary(self, db: Session) -> DashboardSummary:
        counts = self.repository.dashboard_counts(db)
        total = counts["total_scans"]
        counts["approval_rate"] = round((counts["valid_scans"] / total * 100), 1) if total else 0.0
        return DashboardSummary(**counts)


    def _efficiency_metrics(
        self, db: Session, *, line_id: int | None, date_from: datetime | None, date_to: datetime | None
    ) -> dict:
        if line_id is None:
            return {
                "status": "SELECT_LINE", "scope": "LINE_PERIOD", "shift_count": 0,
                "gross_scheduled_minutes": 0, "planned_break_minutes": 0, "planned_downtime_minutes": 0,
                "planned_production_minutes": 0, "unplanned_downtime_minutes": 0, "available_minutes": 0,
                "operational_efficiency_percent": None,
            }
        if date_from is None or date_to is None:
            return {
                "status": "SELECT_PERIOD", "scope": "LINE_PERIOD", "shift_count": 0,
                "gross_scheduled_minutes": 0, "planned_break_minutes": 0, "planned_downtime_minutes": 0,
                "planned_production_minutes": 0, "unplanned_downtime_minutes": 0, "available_minutes": 0,
                "operational_efficiency_percent": None,
            }

        # Os filtros do frontend chegam como UTC naive; os horários de turno/pausa são parâmetros locais.
        range_start_utc = date_from.replace(tzinfo=timezone.utc)
        range_end_utc = date_to.replace(tzinfo=timezone.utc)
        range_start_local = range_start_utc.astimezone(LOCAL_TZ)
        range_end_local = range_end_utc.astimezone(LOCAL_TZ)

        shifts = list(db.scalars(select(WorkShift).where(WorkShift.line_id == line_id, WorkShift.active.is_(True))).all())
        if not shifts:
            return {
                "status": "NO_SHIFT", "scope": "LINE_PERIOD", "shift_count": 0,
                "gross_scheduled_minutes": 0, "planned_break_minutes": 0, "planned_downtime_minutes": 0,
                "planned_production_minutes": 0, "unplanned_downtime_minutes": 0, "available_minutes": 0,
                "operational_efficiency_percent": None,
            }

        shift_ids = [shift.id for shift in shifts]
        breaks = list(db.scalars(select(PlannedBreak).where(PlannedBreak.shift_id.in_(shift_ids), PlannedBreak.active.is_(True))).all())
        breaks_by_shift: dict[int, list[PlannedBreak]] = {}
        for item in breaks:
            breaks_by_shift.setdefault(item.shift_id, []).append(item)

        gross_intervals: list[tuple[datetime, datetime]] = []
        break_intervals: list[tuple[datetime, datetime]] = []
        cursor = range_start_local.date() - timedelta(days=1)
        last_day = range_end_local.date()
        while cursor <= last_day:
            for shift in shifts:
                start_local = datetime.combine(cursor, shift.start_time, LOCAL_TZ)
                end_day = cursor + timedelta(days=1) if shift.crosses_midnight else cursor
                end_local = datetime.combine(end_day, shift.end_time, LOCAL_TZ)
                clipped_start = max(start_local, range_start_local)
                clipped_end = min(end_local, range_end_local)
                if clipped_end <= clipped_start:
                    continue
                gross_intervals.append((clipped_start, clipped_end))
                for planned_break in breaks_by_shift.get(shift.id, []):
                    break_start = datetime.combine(cursor, planned_break.start_time, LOCAL_TZ)
                    break_end_day = cursor
                    if planned_break.start_time < shift.start_time:
                        break_start = datetime.combine(cursor + timedelta(days=1), planned_break.start_time, LOCAL_TZ)
                        break_end_day = cursor + timedelta(days=1)
                    if planned_break.end_time <= planned_break.start_time:
                        break_end_day = break_end_day + timedelta(days=1)
                    break_end = datetime.combine(break_end_day, planned_break.end_time, LOCAL_TZ)
                    b_start = max(break_start, clipped_start)
                    b_end = min(break_end, clipped_end)
                    if b_end > b_start:
                        break_intervals.append((b_start, b_end))
            cursor += timedelta(days=1)

        gross_intervals = _merge_intervals(gross_intervals)
        active_after_breaks = _subtract_intervals(gross_intervals, break_intervals)

        downtime_rows = list(db.scalars(select(DowntimeEvent).where(
            DowntimeEvent.line_id == line_id,
            DowntimeEvent.started_at <= date_to,
            (DowntimeEvent.ended_at.is_(None)) | (DowntimeEvent.ended_at >= date_from),
        )).all())
        now_utc = datetime.now(timezone.utc)
        planned_events: list[tuple[datetime, datetime]] = []
        unplanned_events: list[tuple[datetime, datetime]] = []
        for event in downtime_rows:
            event_start = event.started_at.replace(tzinfo=timezone.utc).astimezone(LOCAL_TZ)
            raw_end = event.ended_at.replace(tzinfo=timezone.utc) if event.ended_at else now_utc
            event_end = raw_end.astimezone(LOCAL_TZ)
            event_start = max(event_start, range_start_local)
            event_end = min(event_end, range_end_local)
            if event_end <= event_start:
                continue
            (planned_events if event.category == "PLANNED" else unplanned_events).append((event_start, event_end))

        planned_downtime = _intersections(active_after_breaks, planned_events)
        planned_production = _subtract_intervals(active_after_breaks, planned_downtime)
        unplanned_downtime = _intersections(planned_production, unplanned_events)
        available = _subtract_intervals(planned_production, unplanned_downtime)

        gross_minutes = _minutes(gross_intervals)
        break_minutes = _minutes(_intersections(gross_intervals, break_intervals))
        planned_stop_minutes = _minutes(planned_downtime)
        planned_minutes = _minutes(planned_production)
        unplanned_minutes = _minutes(unplanned_downtime)
        available_minutes = _minutes(available)
        efficiency = round(available_minutes / planned_minutes * 100, 1) if planned_minutes > 0 else None
        return {
            "status": "OK" if planned_minutes > 0 else "NO_SCHEDULE_IN_PERIOD",
            "scope": "LINE_PERIOD", "shift_count": len(shifts),
            "gross_scheduled_minutes": gross_minutes, "planned_break_minutes": break_minutes,
            "planned_downtime_minutes": planned_stop_minutes, "planned_production_minutes": planned_minutes,
            "unplanned_downtime_minutes": unplanned_minutes, "available_minutes": available_minutes,
            "operational_efficiency_percent": efficiency,
        }

    def operational(
        self,
        db: Session,
        *,
        line_id: int | None = None,
        product_id: int | None = None,
        production_order: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> DashboardOperational:
        payload = self.repository.dashboard_operational(
            db,
            line_id=line_id,
            product_id=product_id,
            production_order=production_order,
            date_from=date_from,
            date_to=date_to,
        )

        # ETAPA 6.8: metas são sempre configuráveis. Para evitar um KPI
        # arbitrário, só aplicamos meta quando uma linha foi explicitamente
        # selecionada. Meta específica do produto tem prioridade; caso não
        # exista, usamos a meta geral da linha como fallback.
        target = None
        source = None
        if line_id is not None:
            if product_id is not None:
                target = self.repository.get_active_target(db, line_id, product_id)
                source = "PRODUCT" if target else None
            if target is None:
                target = self.repository.get_active_target(db, line_id, None)
                source = "LINE" if target else None

        payload["production_target"] = ({
            "id": target.id,
            "line_id": target.line_id,
            "product_id": target.product_id,
            "source": source,
            "hourly_target": target.hourly_target,
            "daily_target": target.daily_target,
            "takt_seconds": target.takt_seconds,
        } if target else None)

        # ETAPAS 6.9.2 a 6.9.4: indicadores calculados somente a partir
        # das unidades realmente adicionadas aos paletes no período filtrado.
        timestamps = payload.pop("_production_timestamps", [])
        intervals = [
            (timestamps[index] - timestamps[index - 1]).total_seconds()
            for index in range(1, len(timestamps))
            if (timestamps[index] - timestamps[index - 1]).total_seconds() > 0
        ]
        average_interval = round(sum(intervals) / len(intervals), 1) if intervals else None
        planned_takt = float(target.takt_seconds) if target and target.takt_seconds is not None else None
        difference = round(average_interval - planned_takt, 1) if average_interval is not None and planned_takt else None
        pace_percent = round(planned_takt / average_interval * 100, 1) if average_interval and planned_takt else None
        if average_interval is None or planned_takt is None:
            pace_status = "NO_DATA"
        elif average_interval <= planned_takt:
            pace_status = "ON_PACE"
        else:
            pace_status = "BELOW_PACE"

        payload["pace"] = {
            "sample_count": len(timestamps),
            "average_interval_seconds": average_interval,
            "planned_takt_seconds": target.takt_seconds if target else None,
            "difference_seconds": difference,
            "pace_percent": pace_percent,
            "status": pace_status,
            "first_unit_at": timestamps[0] if timestamps else None,
            "last_unit_at": timestamps[-1] if timestamps else None,
        }

        hourly_target = target.hourly_target if target else None
        daily_target = target.daily_target if target else None
        for point in payload["production_by_hour"]:
            point["hourly_achievement_percent"] = round(point["quantity"] / hourly_target * 100, 1) if hourly_target else None
            point["daily_achievement_percent"] = round(point["cumulative_quantity"] / daily_target * 100, 1) if daily_target else None

        payload["efficiency"] = self._efficiency_metrics(db, line_id=line_id, date_from=date_from, date_to=date_to)

        # ETAPA 6.12: OEE = Disponibilidade x Performance x Qualidade.
        # Disponibilidade usa a eficiência operacional já validada na 6.11.
        # Performance compara unidades paletizadas com a capacidade teórica do
        # tempo disponível usando o Takt configurado. Para o OEE, o componente
        # é limitado a 100%, evitando que sobrevelocidade compense perdas.
        # Qualidade usa, nesta fase de rastreabilidade, leituras VALID / total
        # de leituras como base objetiva disponível no sistema.
        efficiency = payload["efficiency"]
        availability = efficiency.get("operational_efficiency_percent") if efficiency else None
        available_minutes = efficiency.get("available_minutes", 0) if efficiency else 0
        actual_units = int(payload["summary"]["palletized_units"])
        expected_units = None
        performance = None
        if planned_takt and planned_takt > 0 and available_minutes > 0:
            expected_units = round((available_minutes * 60) / planned_takt, 2)
            if expected_units > 0:
                performance = round(min(100.0, actual_units / expected_units * 100), 1)

        quality_total = int(payload["summary"]["total_scans"])
        quality_good = int(payload["summary"]["valid_scans"])
        quality = round(quality_good / quality_total * 100, 1) if quality_total > 0 else None

        if availability is None:
            oee_status = "NO_AVAILABILITY"
        elif performance is None:
            oee_status = "NO_TARGET" if planned_takt is None else "NO_PRODUCTION_TIME"
        elif quality is None:
            oee_status = "NO_QUALITY_DATA"
        else:
            oee_status = "OK"

        oee = None
        if oee_status == "OK":
            oee = round((availability / 100) * (performance / 100) * (quality / 100) * 100, 1)

        payload["oee"] = {
            "status": oee_status,
            "availability_percent": availability,
            "performance_percent": performance,
            "quality_percent": quality,
            "oee_percent": oee,
            "actual_units": actual_units,
            "expected_units": expected_units,
            "quality_good_count": quality_good,
            "quality_total_count": quality_total,
            "quality_basis": "TRACEABILITY_VALID_SCANS",
        }

        payload["indicator_alerts"] = self._indicator_alerts(
            db, line_id=line_id, product_id=product_id, oee=payload["oee"]
        )

        return DashboardOperational(**payload)


    def oee_history(
        self,
        db: Session,
        *,
        line_id: int,
        product_id: int | None = None,
        date_from: date,
        date_to: date,
    ) -> dict:
        if date_to < date_from:
            date_from, date_to = date_to, date_from
        if (date_to - date_from).days > 30:
            date_from = date_to - timedelta(days=30)

        points = []
        cursor = date_from
        while cursor <= date_to:
            local_start = datetime.combine(cursor, time.min, LOCAL_TZ)
            local_end = datetime.combine(cursor + timedelta(days=1), time.min, LOCAL_TZ)
            utc_start = local_start.astimezone(timezone.utc).replace(tzinfo=None)
            utc_end = local_end.astimezone(timezone.utc).replace(tzinfo=None)

            day_data = self.operational(
                db,
                line_id=line_id,
                product_id=product_id,
                production_order=None,
                date_from=utc_start,
                date_to=utc_end,
            )
            oee = day_data.oee
            points.append({
                "date": cursor.isoformat(),
                "availability_percent": oee.availability_percent if oee else None,
                "performance_percent": oee.performance_percent if oee else None,
                "quality_percent": oee.quality_percent if oee else None,
                "oee_percent": oee.oee_percent if oee else None,
                "palletized_units": day_data.summary.palletized_units,
                "total_scans": day_data.summary.total_scans,
                "valid_scans": day_data.summary.valid_scans,
            })
            cursor += timedelta(days=1)

        return {
            "line_id": line_id,
            "product_id": product_id,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "points": points,
        }

    def loss_analysis(
        self,
        db: Session,
        *,
        line_id: int,
        product_id: int | None = None,
        date_from: date,
        date_to: date,
    ) -> dict:
        if date_to < date_from:
            date_from, date_to = date_to, date_from
        if (date_to - date_from).days > 30:
            date_from = date_to - timedelta(days=30)

        local_start = datetime.combine(date_from, time.min, LOCAL_TZ)
        local_end = datetime.combine(date_to + timedelta(days=1), time.min, LOCAL_TZ)
        utc_start = local_start.astimezone(timezone.utc).replace(tzinfo=None)
        utc_end = local_end.astimezone(timezone.utc).replace(tzinfo=None)

        downtime_stmt = select(DowntimeEvent).where(
            DowntimeEvent.line_id == line_id,
            DowntimeEvent.started_at < utc_end,
            (DowntimeEvent.ended_at.is_(None)) | (DowntimeEvent.ended_at >= utc_start),
        )
        if product_id is not None:
            downtime_stmt = downtime_stmt.join(
                ProductionOrder, ProductionOrder.id == DowntimeEvent.production_order_id
            ).where(ProductionOrder.product_id == product_id)
        downtime_rows = list(db.scalars(downtime_stmt).all())

        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        by_reason: dict[str, dict[str, int]] = {}
        planned_minutes = 0
        unplanned_minutes = 0
        for event in downtime_rows:
            start = max(event.started_at, utc_start)
            raw_end = event.ended_at or now_utc
            end = min(raw_end, utc_end)
            if end <= start:
                continue
            minutes = max(1, int(round((end - start).total_seconds() / 60)))
            if event.category == "PLANNED":
                planned_minutes += minutes
            else:
                unplanned_minutes += minutes
                label = (event.reason or "Sem motivo informado").strip() or "Sem motivo informado"
                item = by_reason.setdefault(label, {"minutes": 0, "occurrences": 0})
                item["minutes"] += minutes
                item["occurrences"] += 1

        unplanned_total = sum(item["minutes"] for item in by_reason.values())
        downtime_reasons = [
            {
                "label": label,
                "minutes": values["minutes"],
                "occurrences": values["occurrences"],
                "percent": round(values["minutes"] / unplanned_total * 100, 1) if unplanned_total else 0.0,
            }
            for label, values in sorted(by_reason.items(), key=lambda pair: (-pair[1]["minutes"], pair[0].lower()))
        ]

        scan_stmt = select(ScanEvent).where(
            ScanEvent.line_id == line_id,
            ScanEvent.scanned_at >= utc_start,
            ScanEvent.scanned_at < utc_end,
            ScanEvent.status != "VALID",
        )
        if product_id is not None:
            product = db.get(Product, product_id)
            if product and product.ean:
                # INVALID pode não possuir EAN parseado; para análise por produto
                # só entram ocorrências que conseguiram identificar o mesmo EAN.
                scan_stmt = scan_stmt.where(ScanEvent.ean == product.ean)
            else:
                scan_stmt = scan_stmt.where(ScanEvent.id == -1)
        scan_rows = list(db.scalars(scan_stmt).all())

        status_counts = {"INVALID": 0, "REJECTED": 0, "DUPLICATE": 0}
        by_scan_reason: dict[str, int] = {}
        for row in scan_rows:
            if row.status in status_counts:
                status_counts[row.status] += 1
            reason = (row.error_message or row.error_code or row.status or "Ocorrência").strip()
            by_scan_reason[reason] = by_scan_reason.get(reason, 0) + 1

        scan_total = len(scan_rows)
        scan_reasons = [
            {
                "label": label,
                "count": count,
                "percent": round(count / scan_total * 100, 1) if scan_total else 0.0,
            }
            for label, count in sorted(by_scan_reason.items(), key=lambda pair: (-pair[1], pair[0].lower()))
        ]

        return {
            "line_id": line_id,
            "product_id": product_id,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "planned_downtime_minutes": planned_minutes,
            "unplanned_downtime_minutes": unplanned_minutes,
            "total_downtime_minutes": planned_minutes + unplanned_minutes,
            "downtime_occurrences": len(downtime_rows),
            "scan_occurrences": scan_total,
            "invalid_count": status_counts["INVALID"],
            "rejected_count": status_counts["REJECTED"],
            "duplicate_count": status_counts["DUPLICATE"],
            "downtime_reasons": downtime_reasons,
            "scan_reasons": scan_reasons,
        }

