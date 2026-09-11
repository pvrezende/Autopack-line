from dataclasses import dataclass
from typing import Literal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas.scan import ScanSimulateRequest, ScanSimulationResult
from app.integrations.barcode import BarcodeParseError, parse_elgin_qr
from app.services.scan_service import ScanService


ReaderSource = Literal["SIMULATOR", "HID_USB", "PHYSICAL"]


@dataclass(frozen=True)
class ReaderInput:
    line_id: int
    raw_code: str
    source: ReaderSource = "SIMULATOR"
    code_type: str = "AUTO"


class ReaderGateway:
    """Ponto único de entrada para leituras de QR/barcode.

    ETAPA 7.2 adiciona o adaptador HID/USB preparado para leitores que se comportam
    como teclado. O navegador recebe os caracteres e o ENTER final; o backend só
    recebe o conteúdo já capturado e continua aplicando as mesmas regras de negócio.

    Nenhum dispositivo físico é considerado conectado nesta etapa. A origem
    PHYSICAL continua bloqueada até conhecermos o leitor e seu protocolo real.
    """

    simulator_adapter = "SIMULATOR_READER_V1"
    hid_adapter = "HID_KEYBOARD_V1"

    def __init__(self) -> None:
        self.scan_service = ScanService()

    def status(self) -> dict:
        return {
            "mode": "SIMULATOR",
            "ready": True,
            "hardware_connected": False,
            "active_adapter": self.simulator_adapter,
            "prepared_adapters": [self.simulator_adapter, self.hid_adapter],
            "supported_sources": ["SIMULATOR", "HID_USB"],
            "supported_code_types": ["QR", "BARCODE"],
            "message": "Camada pronta. Modo HID/USB preparado para leitores que funcionam como teclado; hardware físico ainda não conectado.",
        }

    def adapter_for(self, source: ReaderSource) -> str:
        if source == "HID_USB":
            return self.hid_adapter
        return self.simulator_adapter


    def diagnose(self, raw_code: str, source: ReaderSource = "SIMULATOR") -> dict:
        """Analisa uma leitura sem gravar scan, unidade ou auditoria.

        Usado na homologação do leitor para confirmar exatamente o conteúdo
        recebido antes de liberar a ingestão produtiva.
        """
        if source == "PHYSICAL":
            raise HTTPException(
                status_code=409,
                detail="Leitor físico ainda não configurado. O diagnóstico deve usar SIMULATOR ou HID_USB nesta etapa.",
            )
        if source not in {"SIMULATOR", "HID_USB"}:
            raise HTTPException(status_code=422, detail="Origem de leitura não suportada")

        normalized = raw_code.strip()
        if not normalized:
            raise HTTPException(status_code=422, detail="Conteúdo do leitor está vazio")

        field_count = len(normalized.split(";"))
        detected_type = "QR_ESTRUTURADO" if ";" in normalized else "BARCODE_OU_TEXTO"
        try:
            parsed = parse_elgin_qr(normalized)
            return {
                "source": source,
                "adapter": self.adapter_for(source),
                "valid_format": True,
                "detected_type": "QR_ELGIN_5_CAMPOS",
                "normalized_code": normalized,
                "length": len(normalized),
                "field_count": field_count,
                "parsed": parsed.as_dict(),
                "error": None,
                "message": "Formato reconhecido. O diagnóstico não gravou nenhum dado no MySQL.",
            }
        except BarcodeParseError as exc:
            return {
                "source": source,
                "adapter": self.adapter_for(source),
                "valid_format": False,
                "detected_type": detected_type,
                "normalized_code": normalized,
                "length": len(normalized),
                "field_count": field_count,
                "parsed": None,
                "error": str(exc),
                "message": "Conteúdo recebido, mas o formato produtivo ainda não foi reconhecido. Nenhum dado foi gravado.",
            }

    def ingest(self, db: Session, reading: ReaderInput) -> ScanSimulationResult:
        if reading.source == "PHYSICAL":
            raise HTTPException(
                status_code=409,
                detail="Leitor físico ainda não configurado. Use SIMULATOR ou HID_USB até o equipamento real ser definido.",
            )

        if reading.source not in {"SIMULATOR", "HID_USB"}:
            raise HTTPException(status_code=422, detail="Origem de leitura não suportada")

        normalized = reading.raw_code.strip()
        if not normalized:
            raise HTTPException(status_code=422, detail="Conteúdo do leitor está vazio")

        return self.scan_service.simulate(
            db,
            ScanSimulateRequest(line_id=reading.line_id, raw_code=normalized),
        )
