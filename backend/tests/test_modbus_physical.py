from app.integrations.plc.modbus_physical import get_physical_adapter_diagnostic


def test_physical_adapter_is_safe_and_offline_by_default():
    d = get_physical_adapter_diagnostic()
    assert d["stage"] == "7.20"
    assert d["physical_enabled_by_config"] is False
    assert d["activation_allowed"] is False
    assert d["socket_opened"] is False
    assert d["connection_attempted"] is False
    assert d["target"]["host"] == "192.168.0.2"
    assert d["target"]["port"] == 502
    assert d["write_order"] == ["D704-D749", "D700-D703"]
    assert d["reconnect_read_first"] == ["D752", "D754", "D757", "D758", "D760", "D761"]
