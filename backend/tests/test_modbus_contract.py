from app.integrations.plc.modbus_contract import get_modbus_contract


def test_contract_has_expected_network_and_ranges():
    contract = get_modbus_contract()
    assert contract["status"] == "PROPOSAL_NOT_IMPLEMENTED_IN_LADDER"
    assert contract["plc"]["manufacturer"] == "Delta"
    assert contract["plc"]["model"] == "AS228T-A"
    assert contract["plc"]["protocol"] == "MODBUS_TCP"
    assert contract["plc"]["tcp_port"] == 502
    assert contract["write_range"] == "D700-D749"
    assert contract["read_range"] == "D750-D763"


def test_contract_preserves_safety_rules():
    contract = get_modbus_contract()
    assert contract["timing"]["physical_cycle_timeout_allows_automatic_resend"] is False
    assert contract["authority_rules"]["machine_motion_authority"] == "PLC"
    assert contract["authority_rules"]["pallet_capacity_authority"] == "PLC_IHM_RECIPE"
    assert "AP_MACHINE_STATE" in contract["pending_automation"]
    assert "AP_ACTIVE_FAULT_CODE" in contract["pending_automation"]
    assert "MODBUS_REGISTER_OFFSET" in contract["commissioning_validation"]


def test_contract_contains_request_and_completion_sequence_registers():
    contract = get_modbus_contract()
    write_names = {item["name"] for item in contract["write_registers"]}
    read_names = {item["name"] for item in contract["read_registers"]}
    assert {"AP_REQUEST_SEQUENCE", "AP_COMMAND", "AP_SERIAL", "AP_EAN", "AP_OP", "AP_MODEL"} <= write_names
    assert {"AP_ACK_SEQUENCE", "AP_RESULT_CODE", "AP_COMPLETED_SEQUENCE", "AP_COMPLETION_RESULT"} <= read_names
