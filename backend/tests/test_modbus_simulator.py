from app.integrations.plc.modbus_codec import AsciiByteOrder, ModbusPayload
from app.integrations.plc.modbus_simulator import ModbusPlcSimulator, SimulatorConfig, get_simulator_diagnostic


def payload(seq=321, command=1):
    return ModbusPayload(1, 10, seq, command, 0, "AB12", "7908412552656", "000001275033", "HJFE12C2CG")


def test_simulator_accepts_then_completes_same_sequence():
    sim = ModbusPlcSimulator(SimulatorConfig(pallet_capacity=2))
    accepted = sim.submit(payload(), AsciiByteOrder.HIGH_LOW)
    assert accepted["decoded"]["ack_sequence"] == 321
    assert accepted["decoded"]["result_code"] == 1
    assert accepted["decoded"]["machine_flags"]["machine_busy"] is True
    sim.start_cycle()
    sim.complete_cycle(True)
    final = sim.snapshot()["decoded"]
    assert final["completed_sequence"] == 321
    assert final["completion_result"] == 1
    assert final["boxes_on_pallet"] == 1


def test_duplicate_sequence_is_reported_without_new_cycle():
    sim = ModbusPlcSimulator()
    sim.submit(payload(77))
    sim.start_cycle(); sim.complete_cycle(True); sim.neutralize_command()
    duplicate = sim.submit(payload(77))["decoded"]
    assert duplicate["result_code"] == 3
    assert duplicate["ack_sequence"] == 77


def test_busy_blocks_new_request():
    sim = ModbusPlcSimulator()
    sim.submit(payload(10))
    blocked = sim.submit(payload(11))["decoded"]
    assert blocked["result_code"] == 4
    assert blocked["completed_sequence"] == 0


def test_rejection_command_finishes_as_rejected():
    sim = ModbusPlcSimulator()
    result = sim.submit(payload(44, command=2))["decoded"]
    assert result["completed_sequence"] == 44
    assert result["completion_result"] == 2


def test_fault_blocks_request_and_can_be_cleared():
    sim = ModbusPlcSimulator()
    sim.set_fault(99)
    result = sim.submit(payload(55))["decoded"]
    assert result["result_code"] == 5
    assert result["active_fault_code"] == 99
    sim.clear_fault()
    assert sim.snapshot()["decoded"]["machine_flags"]["machine_ready"] is True


def test_heartbeat_wraps_uint16():
    sim = ModbusPlcSimulator()
    sim.plc[751] = 65535
    assert sim.heartbeat_tick() == 0


def test_simulator_keeps_rev03_identity_and_reader_ranges():
    sim = ModbusPlcSimulator()
    assert sim.plc[765] == 2026
    assert sim.plc[764] == 6
    assert sim.plc[766] == 918
    assert sim.plc[778] == 800
    assert sim.plc[779] == 89
    assert set(range(750, 889)) <= set(sim.plc)


def test_simulator_validates_retest_flag_and_original_sequence():
    sim = ModbusPlcSimulator()
    registers = sim.pc.copy()
    registers.update({700: 1, 702: 90, 703: 1, 705: 1 << 4, 749: 0})
    sim.write_payload(registers)
    sim.write_trigger(registers)
    assert sim.plc[753] == 2


def test_diagnostic_keeps_physical_items_pending():
    data = get_simulator_diagnostic()
    assert data["stage"] == "7.19"
    assert data["physical_connection_required"] is False
    assert data["socket_opened"] is False
    assert "ASCII_BYTE_ORDER_AB12" in data["pending_commissioning"]
