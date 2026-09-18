from dataclasses import dataclass
from urllib.parse import urlparse

from app.core.config import settings


class BarcodeParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedBarcode:
    raw_product_code: str
    model: str
    ean: str
    serial_number: str
    production_order: str
    url: str

    def as_dict(self) -> dict[str, str]:
        return {
            "raw_product_code": self.raw_product_code,
            "model": self.model,
            "ean": self.ean,
            "serial_number": self.serial_number,
            "production_order": self.production_order,
            "url": self.url,
        }


def _validate_ean13(value: str) -> None:
    if len(value) != 13 or not value.isdigit():
        raise BarcodeParseError("EAN deve conter 13 dígitos")
    digits = [int(char) for char in value]
    checksum = (10 - (sum(digits[:-1][::2]) + 3 * sum(digits[:-1][1::2])) % 10) % 10
    if checksum != digits[-1]:
        raise BarcodeParseError("Dígito verificador do EAN é inválido")


def parse_elgin_qr(raw_code: str) -> ParsedBarcode:
    delimiter = settings.barcode_delimiter
    fields = [item.strip() for item in settings.barcode_field_order.split(",") if item.strip()]
    allowed = {"model", "ean", "serial", "production_order", "url"}
    if not delimiter or len(delimiter) != 1:
        raise BarcodeParseError("Configuração do delimitador do QR é inválida")
    if len(fields) != len(set(fields)) or not {"model", "ean", "serial", "production_order"}.issubset(fields) or set(fields) - allowed:
        raise BarcodeParseError("Configuração da ordem dos campos do QR é inválida")
    parts = [part.strip() for part in raw_code.strip().split(delimiter)]
    if len(parts) != len(fields):
        raise BarcodeParseError(f"QR deve possuir exatamente {len(fields)} campos separados por '{delimiter}'")

    values = dict(zip(fields, parts, strict=True))
    raw_product_code = values["model"]
    ean = values["ean"]
    serial_number = values["serial"]
    production_order = values["production_order"]
    url = values.get("url", "")
    if not raw_product_code:
        raise BarcodeParseError("Código do produto ausente")
    _validate_ean13(ean)
    if not serial_number:
        raise BarcodeParseError("Número de série ausente")
    if not production_order:
        raise BarcodeParseError("Ordem de produção ausente")
    if url or settings.barcode_url_required:
        parsed_url = urlparse(url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise BarcodeParseError("URL do QR é inválida")

    # O significado do prefixo do primeiro campo ainda não foi confirmado.
    # Por isso o parser preserva o valor bruto; o modelo oficial é obtido
    # posteriormente a partir do cadastro do produto identificado pelo EAN.
    return ParsedBarcode(
        raw_product_code=raw_product_code,
        model=raw_product_code,
        ean=ean,
        serial_number=serial_number,
        production_order=production_order,
        url=url,
    )
