import pytest
from fastapi import HTTPException

from app.integrations.reader import ReaderGateway, ReaderInput


def test_reader_status_exposes_hid_adapter_without_claiming_hardware() -> None:
    status = ReaderGateway().status()
    assert status["mode"] == "SIMULATOR"
    assert status["ready"] is True
    assert status["hardware_connected"] is False
    assert "SIMULATOR" in status["supported_sources"]
    assert "HID_USB" in status["supported_sources"]
    assert "HID_KEYBOARD_V1" in status["prepared_adapters"]


def test_hid_source_uses_hid_adapter() -> None:
    gateway = ReaderGateway()
    assert gateway.adapter_for("HID_USB") == "HID_KEYBOARD_V1"
    assert gateway.adapter_for("SIMULATOR") == "SIMULATOR_READER_V1"


def test_physical_source_is_blocked_until_hardware_exists() -> None:
    gateway = ReaderGateway()
    with pytest.raises(HTTPException) as exc:
        gateway.ingest(None, ReaderInput(line_id=1, raw_code="ABC", source="PHYSICAL"))  # type: ignore[arg-type]
    assert exc.value.status_code == 409


def test_hid_source_reaches_scan_service() -> None:
    gateway = ReaderGateway()

    class FakeScanService:
        def __init__(self) -> None:
            self.payload = None

        def simulate(self, db, payload):
            self.payload = payload
            return "ok"

    fake = FakeScanService()
    gateway.scan_service = fake  # type: ignore[assignment]
    result = gateway.ingest(None, ReaderInput(line_id=1, raw_code="  ABC123  ", source="HID_USB"))  # type: ignore[arg-type]
    assert result == "ok"
    assert fake.payload.line_id == 1
    assert fake.payload.raw_code == "ABC123"


def test_diagnostic_recognizes_valid_qr_without_db() -> None:
    result = ReaderGateway().diagnose(
        "45HJFE12C2CG;7908412552656;ARC062600106197;000001275033;https://www.elgin.com.br",
        "HID_USB",
    )
    assert result["valid_format"] is True
    assert result["adapter"] == "HID_KEYBOARD_V1"
    assert result["field_count"] == 5
    assert result["parsed"]["ean"] == "7908412552656"


def test_diagnostic_reports_invalid_without_raising() -> None:
    result = ReaderGateway().diagnose("ABC123", "SIMULATOR")
    assert result["valid_format"] is False
    assert result["parsed"] is None
    assert result["error"]
