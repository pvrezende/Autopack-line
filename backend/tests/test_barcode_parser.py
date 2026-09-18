import pytest
from app.integrations.barcode import BarcodeParseError, parse_elgin_qr

REAL_SAMPLE = "45HJFE12C2CG;7908412552656;ARC062600106197;000001275033;https://www.elgin.com.br"


def test_parse_real_sample() -> None:
    result = parse_elgin_qr(REAL_SAMPLE)
    assert result.raw_product_code == "45HJFE12C2CG"
    assert result.ean == "7908412552656"
    assert result.serial_number == "ARC062600106197"
    assert result.production_order == "000001275033"


def test_reject_invalid_field_count() -> None:
    with pytest.raises(BarcodeParseError):
        parse_elgin_qr("A;B;C")


def test_reject_invalid_ean() -> None:
    with pytest.raises(BarcodeParseError):
        parse_elgin_qr("45HJFE12C2CG;7908412552657;ARC062600106197;000001275033;https://www.elgin.com.br")


def test_configurable_profile_can_omit_url(monkeypatch) -> None:
    monkeypatch.setattr("app.integrations.barcode.parser.settings.barcode_field_order", "model,ean,serial,production_order")
    monkeypatch.setattr("app.integrations.barcode.parser.settings.barcode_url_required", False)
    parsed = parse_elgin_qr("45HJFE12C2CG;7908412552656;ARC062600106197;000001275033")
    assert parsed.url == ""
