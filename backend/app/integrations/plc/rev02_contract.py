from __future__ import annotations

from app.core.config import settings
from .modbus_codec import AsciiByteOrder, decode_ascii_registers, encode_ascii_registers


MACHINE_STATES = {
    0: "Inicialização", 10: "Aguardando permissivos", 30: "Verificando palete",
    40: "Alimentando palete vazio", 50: "Pronta", 60: "Aguardando ACK do robô",
    65: "Aguardando entrada na aplicadora", 66: "Movimentando na aplicadora",
    67: "Aplicando fita", 80: "Aguardando coleta", 90: "Aguardando depósito",
    100: "Palete completo", 110: "Descarregando palete", 900: "Falha",
}

RECIPES = {
    1: ("Outdoor 9.000", True), 2: ("Outdoor 12.000", True),
    3: ("Outdoor 18.000", False), 4: ("Outdoor 24.000", False),
    5: ("Outdoor 30.000", False), 6: ("Outdoor 36.000 HD-MBO", False),
    7: ("Outdoor 36.000 HGFE", False), 8: ("Outdoor 36.000 HGQE", False),
}

FEATURE_FLAGS = {
    0: "dashboard_d700_d779", 1: "retest", 2: "reader_status_valid",
    3: "reader_raw_valid", 4: "reader_parsed_fields_valid",
}

READER_STATES = {0: "INACTIVE", 1: "IDLE", 2: "TRIGGER", 3: "READING", 4: "DATA_READY", 5: "ERROR"}
READER_RESULTS = {0: "NONE", 1: "GOOD", 2: "NO_READ", 3: "COMM_ERROR", 4: "INVALID_FORMAT"}


def decode_features(value: int) -> dict[str, bool]:
    return {name: bool(value & (1 << bit)) for bit, name in FEATURE_FLAGS.items()}


def decode_reader_block(registers: dict[int, int], byte_order: AsciiByteOrder = AsciiByteOrder.HIGH_LOW) -> dict:
    missing = [address for address in range(800, 880) if address not in registers]
    if missing:
        raise ValueError(f"Bloco do leitor incompleto: D{missing[0]} ausente")

    def text(length_address: int, start: int, end: int, limit: int) -> str:
        length = registers[length_address]
        if length < 0 or length > limit:
            raise ValueError(f"Comprimento inválido em D{length_address}: {length}")
        return decode_ascii_registers((registers[x] for x in range(start, end + 1)), length, byte_order)

    return {
        "sequence": registers[800],
        "result": registers[801],
        "result_name": READER_RESULTS.get(registers[801], "UNKNOWN"),
        "payload_flags": registers[802],
        "serial": text(803, 804, 819, 32),
        "ean": text(820, 821, 827, 14),
        "production_order": text(828, 829, 836, 16),
        "model": text(837, 838, 845, 16),
        "raw": text(846, 847, 878, 64),
        "error_code": registers[879],
    }


def sample_reader_registers() -> dict[int, int]:
    registers = {address: 0 for address in range(800, 880)}
    values = {
        "serial": (803, 804, "ARC881493129837", 32),
        "ean": (820, 821, "7908412552656", 14),
        "production_order": (828, 829, "000001275033", 16),
        "model": (837, 838, "HJFE12C2CG", 16),
        "raw": (846, 847, "AB12;7908412552656;ARC881493129837;000001275033", 64),
    }
    registers[800], registers[801], registers[802] = 42, 1, 0b11111
    for _, (length_address, start, value, limit) in values.items():
        registers[length_address] = len(value)
        for offset, word in enumerate(encode_ascii_registers(value, limit, AsciiByteOrder.HIGH_LOW)):
            registers[start + offset] = word
    return registers


def get_rev02_diagnostic() -> dict:
    initial_features = decode_features(3)
    sample_reader = decode_reader_block(sample_reader_registers())
    return {
        "stage": "7.33",
        "reference": "ADENDO_INTERFACE_AUTOPACKLINE_REV02_2026-09-17",
        "status": "REV02_READY_OFFLINE_PHYSICAL_READ_BLOCKED",
        "ladder": {"file": "CLP_COMAU_rev04_autopackline.MPU", "revision": 4, "year": 2026, "mmdd": 917, "compiled_in_ispsoft": False, "validated_on_plc": False},
        "connection": {
            "host": settings.plc_modbus_host, "port": settings.plc_modbus_port,
            "unit_id": settings.plc_modbus_unit_id, "pc_ip": settings.plc_pc_ip,
            "netmask": settings.plc_netmask, "address_base": settings.plc_modbus_address_base,
            "ascii_byte_order": settings.plc_ascii_byte_order,
            "physical_enabled": settings.plc_physical_enabled,
            "read_only_enabled": settings.plc_read_only_enabled,
            "socket_opened": False,
        },
        "ranges": {"pc_to_plc": "D700-D749", "plc_status": "D750-D779", "reader": "D800-D879"},
        "identity_probe": {"D750": 1, "D764": 4, "D765": 2026, "D766": 917},
        "machine_states": [{"code": code, "label": label} for code, label in MACHINE_STATES.items()],
        "recipes": [{"id": key, "name": value[0], "released": value[1]} for key, value in RECIPES.items()],
        "reader": {
            "architecture": "SR-1000 -> EtherNet/IP -> CLP Delta -> Modbus TCP -> AUTOPACKLINE",
            "state_codes": READER_STATES, "result_codes": READER_RESULTS,
            "feature_flags_initial_value": 3, "features": initial_features,
            "block_start": 800, "block_length": 80, "audit_source": "D847-D878",
            "sample_decode": sample_reader,
        },
        "retest": {"authorized_flag": "D705.4", "original_sequence": "D749", "history_authority": "AUTOPACKLINE", "deposited_unit_requires_rework": True},
        "ab12": {"text": "AB12", "words": ["0x4142", "0x3132"], "confirmed_order": "HIGH_LOW"},
        "safety_gates": [
            "Rev.04 aberta e compilada no ISPSoft", "Rev.04 comparada e validada no CLP",
            "IP 192.168.29.10 aprovado pela TI", "porta física do switch confirmada",
            "offset 0-based/1-based validado", "byte order AB12 validado fisicamente",
            "assemblies EtherNet/IP do SR-1000 integrados e validados",
        ],
        "message": "Contrato Rev.02, dois blocos e diagnósticos preparados offline. Nenhum socket físico é aberto e nenhuma escrita real é executada nesta etapa.",
    }
