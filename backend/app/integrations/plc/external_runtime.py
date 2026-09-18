from __future__ import annotations

from datetime import datetime
from threading import Lock
import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.reader import ReaderGateway, ReaderInput
from app.models.plc_reader_event import PlcReaderEvent
from app.models.plc_transaction import PlcTransaction
from app.models.product import Product

from .external_simulator import ExternalPlcSimulatorAdapter
from .gateway import PlcConfirmation, PlcGateway
from .modbus_codec import AsciiByteOrder, ModbusPayload, build_write_registers
from .modbus_reconciliation import ACTIVE_TRANSACTION_STATUSES, PlcTransactionStore


class ExternalSimulatorRuntime:
    """Executa o contrato produtivo contra o CLP-Simulator via Modbus TCP.

    A classe nunca seleciona o adaptador físico. Cada tick primeiro lê e
    reconcilia o estado do simulador; só depois considera uma nova leitura.
    """

    def __init__(self) -> None:
        self.adapter = ExternalPlcSimulatorAdapter()
        self.reader_gateway = ReaderGateway()
        self.plc_gateway = PlcGateway()
        self.store = PlcTransactionStore()
        self._lock = Lock()
        self._heartbeat = 0
        self._last_heartbeat_at = 0.0

    def _write_heartbeat_if_due(self) -> None:
        now = time.monotonic()
        if now - self._last_heartbeat_at < 1.0:
            return
        self._heartbeat = (self._heartbeat + 1) & 0xFFFF
        self.adapter.write_registers(701, [self._heartbeat])
        self._last_heartbeat_at = now

    @staticmethod
    def _next_sequence(db: Session) -> int:
        current = int(db.scalar(select(func.max(PlcTransaction.request_sequence))) or 0)
        for offset in range(1, 0x10000):
            candidate = ((current + offset - 1) % 0xFFFF) + 1
            exists = db.scalar(select(PlcTransaction.id).where(PlcTransaction.request_sequence == candidate).limit(1))
            if exists is None:
                return candidate
        raise RuntimeError("Não existe REQUEST_SEQUENCE disponível")

    @staticmethod
    def _result(result: str, message: str, **extra) -> dict:
        return {"result": result, "message": message, **extra}

    def _reconcile_active(self, db: Session, tx: PlcTransaction, probe: dict) -> dict:
        status = probe["handshake"]
        flags = status["machine_flags"]
        tx.ack_sequence = status["ack_sequence"]
        tx.result_code = status["result_code"]
        tx.completed_sequence = status["completed_sequence"]
        tx.completion_result = status["completion_result"]
        tx.pallet_sequence = status["pallet_sequence"]
        tx.boxes_on_pallet = status["boxes_on_pallet"]

        if status["completed_sequence"] == tx.request_sequence and status["completion_result"] in {1, 2, 3}:
            if status["completion_result"] == 1:
                outcome = self.plc_gateway.process(
                    db,
                    PlcConfirmation(line_id=tx.line_id, production_unit_id=tx.production_unit_id, source="SIMULATOR"),
                )
                if outcome.confirmation_status not in {"CONFIRMED", "DUPLICATE_BLOCKED"}:
                    tx.last_error = outcome.message
                    tx.status = "RECONCILE_REQUIRED"
                    db.commit()
                    return self._result("INTERVENTION", outcome.message, transaction_id=tx.id)
                tx.status = "COMPLETED_PLACED"
            elif status["completion_result"] == 2:
                outcome = self.plc_gateway.process(
                    db,
                    PlcConfirmation(
                        line_id=tx.line_id,
                        production_unit_id=tx.production_unit_id,
                        source="SIMULATOR",
                        signal="PALLETIZE_REJECTED",
                        rejection_reason="D761=2 recebido do CLP-Simulator",
                    ),
                )
                tx.status = "COMPLETED_REJECTED"
                tx.last_error = outcome.message
            else:
                tx.status = "COMPLETED_ABORTED"
                tx.last_error = "D761=3: ciclo abortado; intervenção necessária"
            tx.resolved_at = datetime.utcnow()
            self.adapter.write_registers(703, [0])
            db.commit()
            return self._result(tx.status, tx.last_error or "Transação concluída e D703 neutralizado.", transaction_id=tx.id)

        if status["ack_sequence"] == tx.request_sequence:
            if status["result_code"] == 1:
                tx.status = "WAITING_CYCLE_COMPLETION" if flags["machine_busy"] else "REQUEST_ACCEPTED"
                db.commit()
                return self._result(tx.status, "ACK recebido; aguardando D760/D761.", transaction_id=tx.id)
            if status["result_code"] in {2, 3, 4, 5, 7}:
                tx.status = "RECONCILE_REQUIRED"
                tx.last_error = f"CLP-Simulator respondeu D753={status['result_code']}"
                db.commit()
                return self._result("INTERVENTION", tx.last_error, transaction_id=tx.id)

        tx.status = "WAITING_ACK"
        db.commit()
        return self._result("WAITING_ACK", "Aguardando D752/D753 da mesma sequência.", transaction_id=tx.id)

    def tick(self, db: Session, *, line_id: int) -> dict:
        if not settings.plc_external_simulator_enabled:
            return self._result("DISABLED", "Integração com CLP-Simulator desabilitada.")
        if not settings.plc_external_simulator_write_enabled:
            return self._result("READ_ONLY", "Leitura disponível, mas escrita no CLP-Simulator está desabilitada.")

        with self._lock:
            try:
                self._write_heartbeat_if_due()
                probe = self.adapter.probe()
                if not probe.get("connected"):
                    active = self.store.get_active_for_line(db, line_id)
                    if active:
                        active.status = "COMMUNICATION_LOST"
                        active.last_error = probe.get("message", "Falha Modbus")[:120]
                        db.commit()
                    return self._result("COMMUNICATION_LOST", probe.get("message", "Falha Modbus"), probe=probe.get("probe"))

                active = self.store.get_active_for_line(db, line_id)
                if active:
                    return {**self._reconcile_active(db, active, probe), "communication": probe["handshake"]}

                status = probe["handshake"]
                flags = status["machine_flags"]
                if not flags["machine_ready"] or flags["machine_busy"] or flags["machine_fault"] or flags["maintenance_mode"]:
                    return self._result("MACHINE_BLOCKED", "Máquina não está em READY=1, BUSY=0 e FAULT=0.", communication=status)

                reader = probe.get("reader")
                if not reader:
                    return self._result("WAITING_READER", "Nenhuma leitura válida anunciada por D777.", communication=status)
                sequence = int(reader["sequence"])
                previous = db.scalar(select(PlcReaderEvent).where(PlcReaderEvent.reader_sequence == sequence))
                if previous:
                    return self._result("READER_ALREADY_PROCESSED", previous.message or "Leitura já processada.", reader_sequence=sequence, communication=status)

                event = PlcReaderEvent(
                    reader_sequence=sequence,
                    reader_result=int(reader["result"]),
                    raw_data=reader.get("raw"),
                    processing_status="RECEIVED",
                )
                db.add(event)
                db.flush()
                if reader["result"] != 1:
                    event.processing_status = reader["result_name"]
                    event.message = f"Leitor retornou {reader['result_name']}; nenhuma unidade foi enviada."
                    db.commit()
                    return self._result(event.processing_status, event.message, reader_sequence=sequence, communication=status)
                if not reader.get("raw"):
                    event.processing_status = "INVALID_FORMAT"
                    event.message = "GOOD READ sem dado bruto autorizado em D802/D777."
                    db.commit()
                    return self._result(event.processing_status, event.message, reader_sequence=sequence, communication=status)

                scan = self.reader_gateway.ingest(
                    db,
                    ReaderInput(line_id=line_id, raw_code=reader["raw"], source="SIMULATOR", code_type="QR"),
                )
                event.scan_event_id = scan.scan.id
                if scan.scan.status != "VALID" or not scan.unit_id or not scan.production_order_id or not scan.product_id:
                    event.processing_status = scan.scan.status
                    event.message = scan.scan.error_message or f"Leitura finalizada como {scan.scan.status}."
                    db.commit()
                    return self._result(event.processing_status, event.message, reader_sequence=sequence, scan_event_id=scan.scan.id, communication=status)

                product = db.get(Product, scan.product_id)
                if not product or product.plc_recipe_id is None or not product.plc_recipe_released:
                    event.processing_status = "RECIPE_BLOCKED"
                    event.message = "Produto sem receita CLP liberada; configure um ID 1–8 aprovado."
                    db.commit()
                    return self._result(event.processing_status, event.message, reader_sequence=sequence, scan_event_id=scan.scan.id, communication=status)

                request_sequence = self._next_sequence(db)
                payload_dict = {
                    "protocol_version": 1,
                    "pc_heartbeat": self._heartbeat,
                    "request_sequence": request_sequence,
                    "command": 1,
                    "recipe_id": product.plc_recipe_id,
                    "serial": reader.get("serial") or scan.parsed.serial_number,
                    "ean": reader.get("ean") or scan.parsed.ean,
                    "production_order": reader.get("production_order") or scan.parsed.production_order,
                    "model": reader.get("model") or product.model,
                    "retest_authorized": False,
                    "original_request_sequence": 0,
                }
                tx = self.store.persist_before_write(
                    db,
                    line_id=line_id,
                    production_order_id=scan.production_order_id,
                    production_unit_id=scan.unit_id,
                    request_sequence=request_sequence,
                    payload=payload_dict,
                )
                tx.reader_sequence = sequence
                tx.raw_reader_data = reader["raw"]
                event.processing_status = "TRANSACTION_PERSISTED"
                event.message = f"REQUEST_SEQUENCE {request_sequence} persistida antes da escrita."
                db.commit()

                payload = ModbusPayload(**payload_dict)
                registers = build_write_registers(payload, AsciiByteOrder(settings.plc_ascii_byte_order))
                self.adapter.write_registers(704, [registers[address] for address in range(704, 750)])
                self.adapter.write_registers(700, [registers[address] for address in range(700, 704)])
                tx.status = "WAITING_ACK"
                db.commit()
                return self._result(
                    "WAITING_ACK",
                    f"Leitura {sequence} validada; payload e comando enviados com sequência {request_sequence}.",
                    reader_sequence=sequence,
                    request_sequence=request_sequence,
                    transaction_id=tx.id,
                    communication=status,
                )
            except Exception as exc:
                db.rollback()
                return self._result("ERROR", str(exc))


external_simulator_runtime = ExternalSimulatorRuntime()
