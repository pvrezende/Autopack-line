from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable


class AsciiByteOrder(str, Enum):
    HIGH_LOW = "HIGH_LOW"
    LOW_HIGH = "LOW_HIGH"


@dataclass(frozen=True)
class ModbusPayload:
    protocol_version: int
    pc_heartbeat: int
    request_sequence: int
    command: int
    recipe_id: int
    serial: str
    ean: str
    production_order: str
    model: str


RESULT_CODES = {
    0: "NO_RESPONSE",
    1: "REQUEST_ACCEPTED",
    2: "INVALID_DATA",
    3: "DUPLICATE_SEQUENCE",
    4: "MACHINE_BUSY",
    5: "MACHINE_FAULT",
    6: "CYCLE_COMPLETED",
    7: "CYCLE_ABORTED",
}

COMPLETION_RESULTS = {0: "NONE", 1: "PLACED", 2: "REJECTED", 3: "ABORTED"}
PLACE_CONFIRM_SOURCES = {0: "NONE", 1: "ROBOT_PLACE_COMPLETE", 2: "INDEPENDENT_SENSOR_OR_VISION"}

MACHINE_FLAG_BITS = {
    0: "machine_ready",
    1: "machine_busy",
    2: "machine_fault",
    3: "request_accepted",
    4: "unit_placed",
    5: "pallet_complete",
    6: "pallet_change_active",
    7: "maintenance_mode",
    8: "pc_comm_stale",
}


def _uint16(value: int, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > 0xFFFF:
        raise ValueError(f"{field} deve estar entre 0 e 65535")
    return value


def _ascii_bytes(text: str, max_chars: int, field: str) -> bytes:
    if len(text) > max_chars:
        raise ValueError(f"{field} excede o limite de {max_chars} caracteres")
    try:
        encoded = text.encode("ascii", errors="strict")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{field} deve usar ASCII sem acentos") from exc
    return encoded


def encode_ascii_registers(text: str, max_chars: int, byte_order: AsciiByteOrder) -> list[int]:
    raw = _ascii_bytes(text, max_chars, "texto")
    raw = raw.ljust(max_chars, b"\x00")
    if len(raw) % 2:
        raw += b"\x00"
    values: list[int] = []
    for index in range(0, len(raw), 2):
        first, second = raw[index], raw[index + 1]
        if byte_order == AsciiByteOrder.HIGH_LOW:
            values.append((first << 8) | second)
        else:
            values.append((second << 8) | first)
    return values


def decode_ascii_registers(registers: Iterable[int], length: int, byte_order: AsciiByteOrder) -> str:
    if length < 0:
        raise ValueError("length não pode ser negativo")
    raw = bytearray()
    for register in registers:
        value = _uint16(register, "registrador ASCII")
        high = (value >> 8) & 0xFF
        low = value & 0xFF
        if byte_order == AsciiByteOrder.HIGH_LOW:
            raw.extend((high, low))
        else:
            raw.extend((low, high))
    return bytes(raw[:length]).decode("ascii", errors="strict")


def payload_flags(*, serial: str, ean: str, production_order: str, model: str) -> int:
    flags = 0
    if serial:
        flags |= 1 << 0
    if ean:
        flags |= 1 << 1
    if production_order:
        flags |= 1 << 2
    if model:
        flags |= 1 << 3
    return flags


def _place(registers: dict[int, int], start: int, values: Iterable[int]) -> None:
    for offset, value in enumerate(values):
        registers[start + offset] = _uint16(value, f"D{start + offset}")


def build_write_registers(payload: ModbusPayload, byte_order: AsciiByteOrder) -> dict[int, int]:
    """Monta D700-D749 usando endereços lógicos Delta D.

    A função não converte D700 em offset Modbus: esse mapeamento físico permanece
    propositalmente fora do codec até o comissionamento.
    """
    protocol_version = _uint16(payload.protocol_version, "AP_PROTOCOL_VERSION")
    heartbeat = _uint16(payload.pc_heartbeat, "AP_PC_HEARTBEAT")
    request_sequence = _uint16(payload.request_sequence, "AP_REQUEST_SEQUENCE")
    if request_sequence == 0:
        raise ValueError("AP_REQUEST_SEQUENCE deve ser não nulo")
    command = _uint16(payload.command, "AP_COMMAND")
    if command not in {0, 1, 2, 3, 4}:
        raise ValueError("AP_COMMAND deve ser 0, 1, 2, 3 ou 4")
    recipe_id = _uint16(payload.recipe_id, "AP_RECIPE_ID")

    serial = _ascii_bytes(payload.serial, 32, "AP_SERIAL").decode("ascii")
    ean = _ascii_bytes(payload.ean, 14, "AP_EAN").decode("ascii")
    production_order = _ascii_bytes(payload.production_order, 16, "AP_OP").decode("ascii")
    model = _ascii_bytes(payload.model, 16, "AP_MODEL").decode("ascii")

    registers = {address: 0 for address in range(700, 750)}
    # D704-D749 são o payload gravado primeiro.
    registers[704] = recipe_id
    registers[705] = payload_flags(serial=serial, ean=ean, production_order=production_order, model=model)
    registers[706] = len(serial)
    _place(registers, 707, encode_ascii_registers(serial, 32, byte_order))
    registers[723] = len(ean)
    _place(registers, 724, encode_ascii_registers(ean, 14, byte_order))
    registers[731] = len(production_order)
    _place(registers, 732, encode_ascii_registers(production_order, 16, byte_order))
    registers[740] = len(model)
    _place(registers, 741, encode_ascii_registers(model, 16, byte_order))
    registers[749] = 0

    # D700-D703 são deliberadamente montados por último no fluxo de escrita real.
    registers[700] = protocol_version
    registers[701] = heartbeat
    registers[702] = request_sequence
    registers[703] = command
    return registers


def decode_read_registers(registers: dict[int, int]) -> dict:
    missing = [address for address in range(750, 764) if address not in registers]
    if missing:
        raise ValueError(f"Registradores ausentes: {', '.join(f'D{x}' for x in missing)}")
    values = {address: _uint16(registers[address], f"D{address}") for address in range(750, 764)}
    flag_word = values[755]
    flags = {name: bool(flag_word & (1 << bit)) for bit, name in MACHINE_FLAG_BITS.items()}
    return {
        "plc_protocol_version": values[750],
        "plc_heartbeat": values[751],
        "ack_sequence": values[752],
        "result_code": values[753],
        "result_name": RESULT_CODES.get(values[753], "UNKNOWN"),
        "machine_state": values[754],
        "machine_state_text": None,  # tabela D754 pendente da automação
        "machine_flags_word": flag_word,
        "machine_flags": flags,
        "active_fault_code": values[756],
        "active_fault_text": None,  # tabela D756 pendente da automação
        "pallet_sequence": values[757],
        "boxes_on_pallet": values[758],
        "pallet_capacity": values[759],
        "completed_sequence": values[760],
        "completion_result": values[761],
        "completion_result_name": COMPLETION_RESULTS.get(values[761], "UNKNOWN"),
        "place_confirm_source": values[762],
        "place_confirm_source_name": PLACE_CONFIRM_SOURCES.get(values[762], "UNKNOWN"),
        "active_recipe_id": values[763],
    }


def register_map(registers: dict[int, int]) -> list[dict[str, int | str]]:
    return [{"address": f"D{address}", "value": value, "hex": f"0x{value:04X}"} for address, value in sorted(registers.items())]


def get_codec_diagnostic() -> dict:
    sample = ModbusPayload(
        protocol_version=1,
        pc_heartbeat=25,
        request_sequence=1234,
        command=1,
        recipe_id=0,  # relação real de receitas permanece pendente
        serial="AB12",
        ean="7908412552656",
        production_order="000001275033",
        model="HJFE12C2CG",
    )
    high_low = encode_ascii_registers("AB12", 4, AsciiByteOrder.HIGH_LOW)
    low_high = encode_ascii_registers("AB12", 4, AsciiByteOrder.LOW_HIGH)
    default_write = build_write_registers(sample, AsciiByteOrder.HIGH_LOW)
    simulated_read = {
        750: 1, 751: 99, 752: 1234, 753: 1, 754: 0,
        755: (1 << 0) | (1 << 3), 756: 0, 757: 10, 758: 1,
        759: 2, 760: 0, 761: 0, 762: 1, 763: 0,
    }
    return {
        "stage": "7.15",
        "status": "CODEC_READY_BYTE_ORDER_PENDING_COMMISSIONING",
        "logical_addressing_only": True,
        "modbus_register_offset_applied": False,
        "ascii": {
            "encoding": "ASCII",
            "accent_policy": "REJECT_NON_ASCII",
            "characters_per_register": 2,
            "selected_byte_order": None,
            "selection_status": "PENDING_COMMISSIONING_AB12",
            "ab12_probe": {
                "text": "AB12",
                "HIGH_LOW": [f"0x{x:04X}" for x in high_low],
                "LOW_HIGH": [f"0x{x:04X}" for x in low_high],
            },
        },
        "payload_flags": {"serial_bit": 0, "ean_bit": 1, "op_bit": 2, "model_bit": 3},
        "sample_payload": asdict(sample),
        "sample_write_registers_provisional_high_low": register_map(default_write),
        "sample_read_decode": decode_read_registers(simulated_read),
        "write_order": ["D704-D749", "D700-D703"],
        "safety_notes": [
            "O codec usa endereços lógicos D700-D763 e não presume o offset Modbus físico.",
            "Byte order ASCII não é fixado antes do teste AB12 no comissionamento.",
            "Textos fora de ASCII são rejeitados; não há transliteração silenciosa.",
            "D754 e D756 permanecem numéricos até as tabelas aprovadas pela automação serem recebidas.",
        ],
        "message": "Codec UINT16/WORD/ASCII preparado offline. Byte order e offset físico continuam pendentes somente para o comissionamento.",
    }
