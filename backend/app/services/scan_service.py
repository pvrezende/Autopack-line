from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.integrations.barcode import BarcodeParseError, parse_elgin_qr
from app.models.production_unit import ProductionUnit
from app.models.scan_event import ScanEvent
from app.repositories.production_repository import ProductionRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.scan import ScanSimulateRequest, ScanSimulationResult, BarcodeParsed


class ScanService:
    def __init__(self) -> None:
        self.repository = ProductionRepository()
        self.products = ProductRepository()

    def list_page(self, db: Session, **filters):
        return self.repository.list_scans_page(db, **filters)

    def generate_test_qr(self, db: Session, production_order_id: int) -> dict[str, str]:
        """Gera um QR de homologação compatível com a OP selecionada e com serial ainda não usado.

        O código é apenas preparado para teste; nenhuma leitura/unidade é gravada aqui.
        """
        order = self.repository.get_order(db, production_order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Ordem de produção não encontrada")
        if order.status != "ACTIVE":
            raise HTTPException(status_code=409, detail="Selecione uma OP ativa para gerar o QR de teste")
        product = self.products.get(db, order.product_id)
        if not product or not product.active:
            raise HTTPException(status_code=409, detail="Produto da OP não está ativo")
        if not product.ean:
            raise HTTPException(status_code=409, detail="Produto da OP não possui EAN cadastrado")

        # Mantém o formato visual dos seriais reais (ARC + 12 dígitos).
        # O loop também protege contra uma colisão extremamente improvável.
        for _ in range(20):
            serial = f"ARC{uuid4().int % 1_000_000_000_000:012d}"
            if self.repository.get_unit_by_serial(db, serial) is None:
                raw_code = f"{product.sku};{product.ean};{serial};{order.order_number};https://www.elgin.com.br"
                return {
                    "raw_code": raw_code,
                    "serial_number": serial,
                    "production_order": order.order_number,
                    "product_model": product.model,
                    "ean": product.ean,
                }
        raise HTTPException(status_code=503, detail="Não foi possível gerar um serial de teste único; tente novamente")

    def simulate(self, db: Session, payload: ScanSimulateRequest) -> ScanSimulationResult:
        if not self.repository.get_line(db, payload.line_id):
            raise HTTPException(status_code=404, detail="Linha não encontrada")

        try:
            parsed = parse_elgin_qr(payload.raw_code)
        except BarcodeParseError as exc:
            scan = ScanEvent(
                line_id=payload.line_id,
                raw_code=payload.raw_code,
                code_type="QR",
                status="INVALID",
                error_code="QR_FORMAT_INVALID",
                error_message=str(exc),
            )
            db.add(scan)
            db.commit()
            db.refresh(scan)
            return ScanSimulationResult(scan=scan, parsed=None, unit_id=None, product_id=None, production_order_id=None)

        product = self.products.get_by_ean(db, parsed.ean)
        parsed_dict = parsed.as_dict()
        if not product:
            scan = ScanEvent(
                line_id=payload.line_id,
                raw_code=payload.raw_code,
                code_type="QR",
                parsed_data=parsed_dict,
                serial_number=parsed.serial_number,
                ean=parsed.ean,
                production_order=parsed.production_order,
                status="REJECTED",
                error_code="PRODUCT_NOT_REGISTERED",
                error_message=f"EAN {parsed.ean} não está cadastrado",
            )
            db.add(scan)
            db.commit()
            db.refresh(scan)
            return ScanSimulationResult(
                scan=scan,
                parsed=BarcodeParsed(**parsed_dict),
                unit_id=None,
                product_id=None,
                production_order_id=None,
            )

        parsed_dict["model"] = product.model
        existing_unit = self.repository.get_unit_by_serial(db, parsed.serial_number)
        if existing_unit:
            scan = ScanEvent(
                line_id=payload.line_id,
                production_unit_id=existing_unit.id,
                raw_code=payload.raw_code,
                code_type="QR",
                parsed_data=parsed_dict,
                serial_number=parsed.serial_number,
                ean=parsed.ean,
                production_order=parsed.production_order,
                status="DUPLICATE",
                error_code="SERIAL_ALREADY_REGISTERED",
                error_message="Número de série já registrado",
            )
            db.add(scan)
            db.commit()
            db.refresh(scan)
            return ScanSimulationResult(
                scan=scan,
                parsed=BarcodeParsed(**parsed_dict),
                unit_id=existing_unit.id,
                product_id=product.id,
                production_order_id=existing_unit.production_order_id,
            )

        order = self.repository.get_order_by_number(db, parsed.production_order)
        if order and order.product_id != product.id:
            scan = ScanEvent(
                line_id=payload.line_id,
                raw_code=payload.raw_code,
                code_type="QR",
                parsed_data=parsed_dict,
                serial_number=parsed.serial_number,
                ean=parsed.ean,
                production_order=parsed.production_order,
                status="REJECTED",
                error_code="OP_PRODUCT_CONFLICT",
                error_message="A OP já existe vinculada a outro produto",
            )
            db.add(scan)
            db.commit()
            db.refresh(scan)
            return ScanSimulationResult(
                scan=scan,
                parsed=BarcodeParsed(**parsed_dict),
                unit_id=None,
                product_id=product.id,
                production_order_id=order.id,
            )

        if not order:
            scan = ScanEvent(
                line_id=payload.line_id, raw_code=payload.raw_code, code_type="QR", parsed_data=parsed_dict,
                serial_number=parsed.serial_number, ean=parsed.ean, production_order=parsed.production_order,
                status="REJECTED", error_code="OP_NOT_REGISTERED",
                error_message=f"OP {parsed.production_order} não está cadastrada",
            )
            db.add(scan); db.commit(); db.refresh(scan)
            return ScanSimulationResult(scan=scan, parsed=BarcodeParsed(**parsed_dict), unit_id=None, product_id=product.id, production_order_id=None)

        if order.line_id and order.line_id != payload.line_id:
            scan = ScanEvent(
                line_id=payload.line_id, raw_code=payload.raw_code, code_type="QR", parsed_data=parsed_dict,
                serial_number=parsed.serial_number, ean=parsed.ean, production_order=parsed.production_order,
                status="REJECTED", error_code="OP_LINE_CONFLICT",
                error_message="A OP está vinculada a outra linha de produção",
            )
            db.add(scan); db.commit(); db.refresh(scan)
            return ScanSimulationResult(scan=scan, parsed=BarcodeParsed(**parsed_dict), unit_id=None, product_id=product.id, production_order_id=order.id)

        if order.status != "ACTIVE":
            labels = {"OPEN": "aberta", "PAUSED": "pausada", "COMPLETED": "finalizada", "CANCELLED": "cancelada"}
            scan = ScanEvent(
                line_id=payload.line_id, raw_code=payload.raw_code, code_type="QR", parsed_data=parsed_dict,
                serial_number=parsed.serial_number, ean=parsed.ean, production_order=parsed.production_order,
                status="REJECTED", error_code="OP_NOT_ACTIVE",
                error_message=f"OP {parsed.production_order} está {labels.get(order.status, order.status)}; inicie a OP antes da leitura",
            )
            db.add(scan); db.commit(); db.refresh(scan)
            return ScanSimulationResult(scan=scan, parsed=BarcodeParsed(**parsed_dict), unit_id=None, product_id=product.id, production_order_id=order.id)

        unit = ProductionUnit(
            serial_number=parsed.serial_number,
            product_id=product.id,
            production_order_id=order.id,
            status="SCANNED",
        )
        db.add(unit)
        db.flush()

        scan = ScanEvent(
            line_id=payload.line_id,
            production_unit_id=unit.id,
            raw_code=payload.raw_code,
            code_type="QR",
            parsed_data=parsed_dict,
            serial_number=parsed.serial_number,
            ean=parsed.ean,
            production_order=parsed.production_order,
            status="VALID",
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return ScanSimulationResult(
            scan=scan,
            parsed=BarcodeParsed(**parsed_dict),
            unit_id=unit.id,
            product_id=product.id,
            production_order_id=order.id,
        )
