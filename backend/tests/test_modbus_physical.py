from app.integrations.plc.modbus_physical import PhysicalModbusAdapter, get_physical_adapter_diagnostic
from app.integrations.plc.rev02_contract import sample_reader_registers


def test_physical_adapter_is_safe_and_offline_by_default():
    d = get_physical_adapter_diagnostic()
    assert d["stage"] == "7.33.1"
    assert d["physical_enabled_by_config"] is False
    assert d["activation_allowed"] is False
    assert d["socket_opened"] is False
    assert d["connection_attempted"] is False
    assert d["target"]["host"] == "192.168.29.5"
    assert d["target"]["port"] == 502
    assert d["write_order"] == ["D704-D749", "D700-D703"]
    assert d["reconnect_read_first"] == ["D752", "D754", "D757", "D758", "D760", "D761"]


def test_read_only_activation_requires_every_explicit_commissioning_gate(monkeypatch):
    prefix = "app.integrations.plc.modbus_physical.settings."
    monkeypatch.setattr(prefix + "plc_physical_enabled", True)
    monkeypatch.setattr(prefix + "plc_read_only_enabled", True)
    for name in (
        "plc_ispsoft_compiled", "plc_register_offset_validated", "plc_ascii_byte_order_validated",
        "plc_network_validated", "plc_reader_ethernetip_validated", "plc_physical_e2e_authorized",
    ):
        monkeypatch.setattr(prefix + name, True)
    diagnostic = get_physical_adapter_diagnostic()
    assert diagnostic["pending_commissioning"] == []
    assert diagnostic["activation_allowed"] is True
    assert diagnostic["write_allowed"] is False


def test_physical_read_only_probe_uses_direct_delta_addresses_after_minimum_gates(monkeypatch):
    prefix = "app.integrations.plc.modbus_physical.settings."
    for name in ("plc_physical_enabled", "plc_read_only_enabled", "plc_ispsoft_compiled", "plc_register_offset_validated", "plc_network_validated"):
        monkeypatch.setattr(prefix + name, True)

    class FakeClient:
        def __init__(self): self.calls = []
        def read_holding_registers(self, address, count):
            self.calls.append((address, count))
            if address == 800:
                block = sample_reader_registers()
                return [block[x] for x in range(800, 889)]
            values = [0] * 30
            values[0], values[4], values[5] = 1, 50, 1
            values[14], values[15], values[16] = 6, 2026, 918
            values[20] = 42
            values[27], values[28], values[29] = 15, 800, 89
            return values

    client = FakeClient()
    result = PhysicalModbusAdapter().probe_read_only(client)
    assert result["connected"] is True
    assert result["probe"] == "READ_REV03_SNAPSHOT_OK"
    assert client.calls == [(750, 30), (800, 89), (750, 30)]
