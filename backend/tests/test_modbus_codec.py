import pytest

from app.integrations.plc.modbus_codec import (
    AsciiByteOrder,
    ModbusPayload,
    build_write_registers,
    decode_ascii_registers,
    decode_read_registers,
    encode_ascii_registers,
    get_codec_diagnostic,
    payload_flags,
)


def sample_payload(**overrides):
    values = dict(
        protocol_version=1,
        pc_heartbeat=10,
        request_sequence=123,
        command=1,
        recipe_id=7,
        serial="ARC123",
        ean="7908412552656",
        production_order="000001275033",
        model="HJFE12C2CG",
    )
    values.update(overrides)
    return ModbusPayload(**values)


def test_ab12_supports_both_byte_orders_without_guessing_commissioning_value():
    assert encode_ascii_registers("AB12", 4, AsciiByteOrder.HIGH_LOW) == [0x4142, 0x3132]
    assert encode_ascii_registers("AB12", 4, AsciiByteOrder.LOW_HIGH) == [0x4241, 0x3231]
    assert decode_ascii_registers([0x4142, 0x3132], 4, AsciiByteOrder.HIGH_LOW) == "AB12"
    assert decode_ascii_registers([0x4241, 0x3231], 4, AsciiByteOrder.LOW_HIGH) == "AB12"


def test_write_map_places_lengths_flags_and_reserved_register():
    registers = build_write_registers(sample_payload(), AsciiByteOrder.HIGH_LOW)
    assert set(registers) == set(range(700, 750))
    assert registers[700] == 1
    assert registers[702] == 123
    assert registers[703] == 1
    assert registers[704] == 7
    assert registers[705] == 0b1111
    assert registers[706] == len("ARC123")
    assert registers[723] == 13
    assert registers[731] == 12
    assert registers[740] == 10
    assert registers[749] == 0


def test_payload_flags_reflect_only_present_fields():
    assert payload_flags(serial="A", ean="", production_order="OP", model="") == 0b0101


def test_codec_rejects_non_ascii_and_overlength_and_zero_sequence():
    with pytest.raises(ValueError, match="ASCII sem acentos"):
        build_write_registers(sample_payload(model="MÓDULO"), AsciiByteOrder.HIGH_LOW)
    with pytest.raises(ValueError, match="32 caracteres"):
        build_write_registers(sample_payload(serial="X" * 33), AsciiByteOrder.HIGH_LOW)
    with pytest.raises(ValueError, match="não nulo"):
        build_write_registers(sample_payload(request_sequence=0), AsciiByteOrder.HIGH_LOW)


def test_decode_d755_flags_and_completion_fields():
    read = {address: 0 for address in range(750, 764)}
    read.update({750: 1, 751: 55, 752: 123, 753: 6, 755: (1 << 1) | (1 << 4) | (1 << 5), 757: 9, 758: 2, 759: 2, 760: 123, 761: 1, 762: 1})
    decoded = decode_read_registers(read)
    assert decoded["result_name"] == "CYCLE_COMPLETED"
    assert decoded["machine_flags"]["machine_busy"] is True
    assert decoded["machine_flags"]["unit_placed"] is True
    assert decoded["machine_flags"]["pallet_complete"] is True
    assert decoded["completed_sequence"] == 123
    assert decoded["completion_result_name"] == "PLACED"
    assert decoded["place_confirm_source_name"] == "ROBOT_PLACE_COMPLETE"


def test_codec_diagnostic_keeps_commissioning_items_pending():
    diagnostic = get_codec_diagnostic()
    assert diagnostic["stage"] == "7.15"
    assert diagnostic["ascii"]["selected_byte_order"] is None
    assert diagnostic["ascii"]["selection_status"] == "PENDING_COMMISSIONING_AB12"
    assert diagnostic["modbus_register_offset_applied"] is False
    assert diagnostic["write_order"] == ["D704-D749", "D700-D703"]
