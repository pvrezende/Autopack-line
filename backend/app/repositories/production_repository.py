from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.pallet import Pallet
from app.models.pallet_config import PalletConfig
from app.models.pallet_item import PalletItem
from app.models.production_line import ProductionLine
from app.models.production_order import ProductionOrder
from app.models.production_target import ProductionTarget
from app.models.production_unit import ProductionUnit
from app.models.product import Product
from app.models.scan_event import ScanEvent
from app.models.indicator_threshold import IndicatorThreshold


class ProductionRepository:
    def list_lines(self, db: Session) -> list[ProductionLine]:
        return list(db.scalars(select(ProductionLine).order_by(ProductionLine.code)).all())

    def get_line(self, db: Session, line_id: int) -> ProductionLine | None:
        return db.get(ProductionLine, line_id)

    def create_line(self, db: Session, line: ProductionLine) -> ProductionLine:
        db.add(line)
        db.commit()
        db.refresh(line)
        return line

    def get_active_pallet_config(self, db: Session, product_id: int, line_id: int) -> PalletConfig | None:
        return db.scalar(
            select(PalletConfig)
            .where(
                PalletConfig.product_id == product_id,
                PalletConfig.line_id == line_id,
                PalletConfig.active.is_(True),
                PalletConfig.valid_until.is_(None),
            )
            .order_by(PalletConfig.valid_from.desc(), PalletConfig.id.desc())
        )

    def list_pallet_configs(self, db: Session) -> list[PalletConfig]:
        return list(db.scalars(select(PalletConfig).order_by(PalletConfig.id.desc())).all())

    def close_active_pallet_config(self, db: Session, product_id: int, line_id: int, at: datetime) -> None:
        current = self.get_active_pallet_config(db, product_id, line_id)
        if current:
            current.active = False
            current.valid_until = at

    def list_targets(self, db: Session) -> list[ProductionTarget]:
        return list(db.scalars(select(ProductionTarget).order_by(ProductionTarget.id.desc())).all())

    def get_active_target(self, db: Session, line_id: int, product_id: int | None) -> ProductionTarget | None:
        query = select(ProductionTarget).where(
            ProductionTarget.line_id == line_id,
            ProductionTarget.active.is_(True),
            ProductionTarget.valid_until.is_(None),
        )
        if product_id is None:
            query = query.where(ProductionTarget.product_id.is_(None))
        else:
            query = query.where(ProductionTarget.product_id == product_id)
        return db.scalar(query.order_by(ProductionTarget.valid_from.desc(), ProductionTarget.id.desc()))

    def list_indicator_thresholds(self, db: Session) -> list[IndicatorThreshold]:
        return list(db.scalars(select(IndicatorThreshold).order_by(IndicatorThreshold.id.desc())).all())

    def get_active_indicator_threshold(self, db: Session, line_id: int, product_id: int | None) -> IndicatorThreshold | None:
        query = select(IndicatorThreshold).where(
            IndicatorThreshold.line_id == line_id,
            IndicatorThreshold.active.is_(True),
            IndicatorThreshold.valid_until.is_(None),
        )
        if product_id is None:
            query = query.where(IndicatorThreshold.product_id.is_(None))
        else:
            query = query.where(IndicatorThreshold.product_id == product_id)
        return db.scalar(query.order_by(IndicatorThreshold.valid_from.desc(), IndicatorThreshold.id.desc()))

    def get_order_by_number(self, db: Session, order_number: str) -> ProductionOrder | None:
        return db.scalar(select(ProductionOrder).where(ProductionOrder.order_number == order_number))

    def list_orders(self, db: Session) -> list[ProductionOrder]:
        return list(db.scalars(select(ProductionOrder).order_by(ProductionOrder.id.desc())).all())


    def get_order(self, db: Session, order_id: int) -> ProductionOrder | None:
        return db.get(ProductionOrder, order_id)

    def list_orders_page(
        self, db: Session, *, page: int, page_size: int, status: str | None = None,
        line_id: int | None = None, product_id: int | None = None, search: str | None = None,
    ) -> tuple[list[ProductionOrder], int]:
        query = select(ProductionOrder)
        count_query = select(func.count()).select_from(ProductionOrder)
        conditions = []
        if status:
            conditions.append(ProductionOrder.status == status)
        if line_id:
            conditions.append(ProductionOrder.line_id == line_id)
        if product_id:
            conditions.append(ProductionOrder.product_id == product_id)
        if search:
            token = f"%{search.strip()}%"
            conditions.append(ProductionOrder.order_number.like(token))
        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)
        total = int(db.scalar(count_query) or 0)
        items = list(db.scalars(
            query.order_by(ProductionOrder.id.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all())
        return items, total

    def count_units_for_order(self, db: Session, order_id: int) -> int:
        """Conta todas as unidades validamente criadas para a OP, inclusive as ainda aguardando CLP."""
        return int(db.scalar(select(func.count()).select_from(ProductionUnit).where(ProductionUnit.production_order_id == order_id)) or 0)

    def count_palletized_units_for_order(self, db: Session, order_id: int) -> int:
        """Conta somente produção fisicamente confirmada pelo ciclo de paletização/CLP."""
        return int(db.scalar(
            select(func.count()).select_from(ProductionUnit).where(
                ProductionUnit.production_order_id == order_id,
                ProductionUnit.status == "PALLETIZED",
            )
        ) or 0)

    def count_pallets_for_order(self, db: Session, order_id: int, pallet_status: str) -> int:
        return int(db.scalar(select(func.count()).select_from(Pallet).where(Pallet.production_order_id == order_id, Pallet.status == pallet_status)) or 0)

    def get_unit(self, db: Session, unit_id: int) -> ProductionUnit | None:
        return db.get(ProductionUnit, unit_id)

    def get_unit_by_serial(self, db: Session, serial: str) -> ProductionUnit | None:
        return db.scalar(select(ProductionUnit).where(ProductionUnit.serial_number == serial))

    def list_scans_page(
        self, db: Session, *, page: int, page_size: int, status: str | None = None, line_id: int | None = None,
        serial: str | None = None, ean: str | None = None, production_order: str | None = None,
        date_from: datetime | None = None, date_to: datetime | None = None,
    ) -> tuple[list[ScanEvent], int]:
        query = select(ScanEvent)
        count_query = select(func.count()).select_from(ScanEvent)
        conditions = []
        if status:
            if status == "OCCURRENCES":
                conditions.append(ScanEvent.status.in_(["INVALID", "REJECTED", "DUPLICATE"]))
            else:
                conditions.append(ScanEvent.status == status)
        if line_id:
            conditions.append(ScanEvent.line_id == line_id)
        if serial:
            conditions.append(ScanEvent.serial_number.like(f"{serial}%"))
        if ean:
            conditions.append(ScanEvent.ean == ean)
        if production_order:
            conditions.append(ScanEvent.production_order.like(f"{production_order}%"))
        if date_from:
            conditions.append(ScanEvent.scanned_at >= date_from)
        if date_to:
            conditions.append(ScanEvent.scanned_at <= date_to)
        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)
        total = db.scalar(count_query) or 0
        items = list(db.scalars(
            query.order_by(ScanEvent.id.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all())
        return items, total


    def get_scan(self, db: Session, scan_id: int) -> ScanEvent | None:
        return db.get(ScanEvent, scan_id)

    def list_scans_export(self, db: Session, **filters) -> list[ScanEvent]:
        _, total = self.list_scans_page(db, page=1, page_size=100, **filters)
        items = []
        for page in range(1, (total + 99) // 100 + 1):
            batch, _ = self.list_scans_page(db, page=page, page_size=100, **filters)
            items.extend(batch)
        return items

    def get_pallet(self, db: Session, pallet_id: int) -> Pallet | None:
        return db.get(Pallet, pallet_id)

    def get_pallet_detail(self, db: Session, pallet_id: int):
        pallet = db.get(Pallet, pallet_id)
        if not pallet:
            return None
        order = db.get(ProductionOrder, pallet.production_order_id)
        line = db.get(ProductionLine, pallet.line_id)
        from app.models.product import Product
        product = db.get(Product, pallet.product_id)
        rows = db.execute(
            select(PalletItem, ProductionUnit).join(ProductionUnit, PalletItem.production_unit_id == ProductionUnit.id)
            .where(PalletItem.pallet_id == pallet_id).order_by(PalletItem.sequence_number)
        ).all()
        return pallet, order, line, product, rows

    def list_pallets_export(self, db: Session, **filters) -> list[Pallet]:
        _, total = self.list_pallets_page(db, page=1, page_size=100, **filters)
        items = []
        for page in range(1, (total + 99) // 100 + 1):
            batch, _ = self.list_pallets_page(db, page=page, page_size=100, **filters)
            items.extend(batch)
        return items

    def get_open_pallet_for_update(
        self, db: Session, line_id: int, product_id: int, production_order_id: int
    ) -> Pallet | None:
        return db.scalar(
            select(Pallet)
            .where(
                Pallet.line_id == line_id,
                Pallet.product_id == product_id,
                Pallet.production_order_id == production_order_id,
                Pallet.status == "OPEN",
            )
            .order_by(Pallet.id.desc())
            .with_for_update()
        )

    def list_pallets_page(
        self, db: Session, *, page: int, page_size: int, status: str | None = None, line_id: int | None = None,
        product_id: int | None = None, pallet_code: str | None = None, production_order: str | None = None,
        date_from: datetime | None = None, date_to: datetime | None = None,
    ) -> tuple[list[Pallet], int]:
        query = select(Pallet)
        count_query = select(func.count()).select_from(Pallet)
        conditions = []
        if status:
            conditions.append(Pallet.status == status)
        if line_id:
            conditions.append(Pallet.line_id == line_id)
        if product_id:
            conditions.append(Pallet.product_id == product_id)
        if pallet_code:
            conditions.append(Pallet.pallet_code.like(f"{pallet_code}%"))
        if date_from:
            conditions.append(Pallet.opened_at >= date_from)
        if date_to:
            conditions.append(Pallet.opened_at <= date_to)
        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)
        if production_order:
            query = query.join(ProductionOrder, Pallet.production_order_id == ProductionOrder.id).where(
                ProductionOrder.order_number.like(f"{production_order}%")
            )
            count_query = count_query.join(ProductionOrder, Pallet.production_order_id == ProductionOrder.id).where(
                ProductionOrder.order_number.like(f"{production_order}%")
            )
        total = db.scalar(count_query) or 0
        items = list(db.scalars(
            query.order_by(Pallet.id.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all())
        return items, total

    def get_pallet_item_by_unit(self, db: Session, unit_id: int) -> PalletItem | None:
        return db.scalar(select(PalletItem).where(PalletItem.production_unit_id == unit_id))

    def dashboard_counts(self, db: Session) -> dict[str, int]:
        total_scans = db.scalar(select(func.count()).select_from(ScanEvent)) or 0
        valid_scans = db.scalar(select(func.count()).select_from(ScanEvent).where(ScanEvent.status == "VALID")) or 0
        invalid_scans = db.scalar(
            select(func.count()).select_from(ScanEvent).where(ScanEvent.status.in_(["INVALID", "REJECTED", "DUPLICATE"]))
        ) or 0
        open_pallets = db.scalar(select(func.count()).select_from(Pallet).where(Pallet.status == "OPEN")) or 0
        completed_pallets = db.scalar(select(func.count()).select_from(Pallet).where(Pallet.status == "FULL")) or 0
        palletized_units = db.scalar(select(func.count()).select_from(PalletItem)) or 0
        return {
            "total_scans": total_scans,
            "valid_scans": valid_scans,
            "invalid_scans": invalid_scans,
            "open_pallets": open_pallets,
            "completed_pallets": completed_pallets,
            "palletized_units": palletized_units,
        }


    def dashboard_operational(
        self, db: Session, *, line_id: int | None = None, product_id: int | None = None,
        production_order: str | None = None, date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict:
        scan_conditions = []
        pallet_identity_conditions = []
        item_conditions = []

        if line_id:
            scan_conditions.append(ScanEvent.line_id == line_id)
            pallet_identity_conditions.append(Pallet.line_id == line_id)
        if product_id:
            product = db.get(Product, product_id)
            if product and product.ean:
                scan_conditions.append(ScanEvent.ean == product.ean)
            else:
                scan_conditions.append(ScanEvent.id == -1)
            pallet_identity_conditions.append(Pallet.product_id == product_id)
        if production_order:
            scan_conditions.append(ScanEvent.production_order.like(f"{production_order}%"))
        if date_from:
            scan_conditions.append(ScanEvent.scanned_at >= date_from)
            item_conditions.append(PalletItem.added_at >= date_from)
        if date_to:
            scan_conditions.append(ScanEvent.scanned_at <= date_to)
            item_conditions.append(PalletItem.added_at <= date_to)

        def scan_count(extra=None):
            q = select(func.count()).select_from(ScanEvent)
            conditions = list(scan_conditions)
            if extra is not None:
                conditions.append(extra)
            if conditions:
                q = q.where(*conditions)
            return int(db.scalar(q) or 0)

        total_scans = scan_count()
        valid_scans = scan_count(ScanEvent.status == "VALID")
        invalid_scans = scan_count(ScanEvent.status.in_(["INVALID", "REJECTED", "DUPLICATE"]))

        pallet_base = select(func.count()).select_from(Pallet)
        pallet_identity = list(pallet_identity_conditions)
        if production_order:
            pallet_base = pallet_base.join(ProductionOrder, Pallet.production_order_id == ProductionOrder.id)
            pallet_identity.append(ProductionOrder.order_number.like(f"{production_order}%"))

        # Paletes abertos representam o estado atual da linha e não desaparecem
        # por terem sido abertos antes do início do período selecionado.
        open_q = pallet_base.where(*pallet_identity, Pallet.status == "OPEN")
        open_pallets_count = int(db.scalar(open_q) or 0)

        full_conditions = list(pallet_identity)
        full_conditions.append(Pallet.status == "FULL")
        if date_from:
            full_conditions.append(Pallet.completed_at >= date_from)
        if date_to:
            full_conditions.append(Pallet.completed_at <= date_to)
        completed_pallets = int(db.scalar(pallet_base.where(*full_conditions)) or 0)

        item_q = select(func.count()).select_from(PalletItem).join(Pallet, PalletItem.pallet_id == Pallet.id)
        item_filters = list(item_conditions)
        if line_id:
            item_filters.append(Pallet.line_id == line_id)
        if product_id:
            item_filters.append(Pallet.product_id == product_id)
        if production_order:
            item_q = item_q.join(ProductionOrder, Pallet.production_order_id == ProductionOrder.id)
            item_filters.append(ProductionOrder.order_number.like(f"{production_order}%"))
        if item_filters:
            item_q = item_q.where(*item_filters)
        palletized_units = int(db.scalar(item_q) or 0)

        hourly_q = (
            select(PalletItem.added_at)
            .select_from(PalletItem)
            .join(Pallet, PalletItem.pallet_id == Pallet.id)
        )
        hourly_filters = list(item_conditions)
        if line_id:
            hourly_filters.append(Pallet.line_id == line_id)
        if product_id:
            hourly_filters.append(Pallet.product_id == product_id)
        if production_order:
            hourly_q = hourly_q.join(ProductionOrder, Pallet.production_order_id == ProductionOrder.id)
            hourly_filters.append(ProductionOrder.order_number.like(f"{production_order}%"))
        if hourly_filters:
            hourly_q = hourly_q.where(*hourly_filters)
        production_timestamps = sorted(list(db.scalars(hourly_q.order_by(PalletItem.added_at.asc())).all()))
        hour_counts: dict[int, int] = {}
        for added_at in production_timestamps:
            hour_counts[added_at.hour] = hour_counts.get(added_at.hour, 0) + 1
        cumulative = 0
        production_by_hour = []
        for hour in sorted(hour_counts):
            cumulative += hour_counts[hour]
            production_by_hour.append({"hour": f"{hour:02d}:00", "quantity": hour_counts[hour], "cumulative_quantity": cumulative})

        status_q = select(ScanEvent.status, func.count()).select_from(ScanEvent)
        if scan_conditions:
            status_q = status_q.where(*scan_conditions)
        status_rows = db.execute(status_q.group_by(ScanEvent.status)).all()
        status_map = {status: int(qty) for status, qty in status_rows}
        scan_statuses = [{"status": status, "quantity": status_map.get(status, 0)} for status in ["VALID", "INVALID", "REJECTED", "DUPLICATE"]]

        open_list_q = (
            select(Pallet, ProductionLine, Product, ProductionOrder)
            .join(ProductionLine, Pallet.line_id == ProductionLine.id)
            .join(Product, Pallet.product_id == Product.id)
            .join(ProductionOrder, Pallet.production_order_id == ProductionOrder.id)
            .where(Pallet.status == "OPEN")
        )
        if pallet_identity_conditions:
            open_list_q = open_list_q.where(*pallet_identity_conditions)
        if production_order:
            open_list_q = open_list_q.where(ProductionOrder.order_number.like(f"{production_order}%"))
        open_rows = db.execute(open_list_q.order_by(Pallet.opened_at.desc()).limit(8)).all()
        open_pallets = [{
            "id": pallet.id,
            "pallet_code": pallet.pallet_code,
            "line_id": pallet.line_id,
            "line_code": line.code,
            "product_id": pallet.product_id,
            "product_model": product.model,
            "production_order": order.order_number,
            "current_quantity": pallet.current_quantity,
            "target_quantity": pallet.target_quantity,
            "progress_percent": round((pallet.current_quantity / pallet.target_quantity * 100), 1) if pallet.target_quantity else 0.0,
            "opened_at": pallet.opened_at,
        } for pallet, line, product, order in open_rows]

        occurrence_q = (
            select(ScanEvent, ProductionLine)
            .join(ProductionLine, ScanEvent.line_id == ProductionLine.id)
            .where(ScanEvent.status.in_(["INVALID", "REJECTED", "DUPLICATE"]))
        )
        if scan_conditions:
            occurrence_q = occurrence_q.where(*scan_conditions)
        occurrence_rows = db.execute(occurrence_q.order_by(ScanEvent.scanned_at.desc()).limit(8)).all()
        recent_occurrences = [{
            "id": scan.id,
            "status": scan.status,
            "serial_number": scan.serial_number,
            "line_id": scan.line_id,
            "line_code": line.code,
            "error_message": scan.error_message,
            "scanned_at": scan.scanned_at,
        } for scan, line in occurrence_rows]

        return {
            "summary": {
                "total_scans": total_scans,
                "valid_scans": valid_scans,
                "invalid_scans": invalid_scans,
                "approval_rate": round((valid_scans / total_scans * 100), 1) if total_scans else 0.0,
                "open_pallets": open_pallets_count,
                "completed_pallets": completed_pallets,
                "palletized_units": palletized_units,
            },
            "production_by_hour": production_by_hour,
            "scan_statuses": scan_statuses,
            "open_pallets": open_pallets,
            "recent_occurrences": recent_occurrences,
            "_production_timestamps": production_timestamps,
        }
