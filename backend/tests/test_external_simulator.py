import pytest

from app.integrations.plc.external_simulator import ExternalPlcSimulatorAdapter, ExternalSimulatorConfig
from app.integrations.plc.rev02_contract import sample_reader_registers


class FakeClient:
    def __init__(self):
        self.calls = []

    def read_holding_registers(self, address: int, count: int) -> list[int]:
        self.calls.append((address, count))
        if address == 50:
            values = [0] * 30
            values[0], values[4], values[5] = 1, 50, 1
            values[14], values[15], values[16] = 4, 2026, 917
            values[20], values[27], values[28], values[29] = 42, 0b11111, 800, 80
            return values
        if address == 100:
            block = sample_reader_registers()
            return [block[x] for x in range(800, 880)]
        raise AssertionError((address, count))

    def write_holding_registers(self, address: int, values: list[int]) -> None:
        self.calls.append((address, values))


def config():
    return ExternalSimulatorConfig("127.0.0.1", 1502, 1, 700, 0, 1000)


def test_external_simulator_maps_complete_rev02_contract():
    mapping = config()
    assert mapping.address_for(700) == 0
    assert mapping.address_for(779) == 79
    assert mapping.address_for(800) == 100
    assert mapping.address_for(879) == 179


def test_external_simulator_probe_reads_consistent_snapshot(monkeypatch):
    monkeypatch.setattr("app.integrations.plc.external_simulator.settings.plc_external_simulator_enabled", True)
    result = ExternalPlcSimulatorAdapter(config()).probe(FakeClient())
    assert result["connected"] is True
    assert result["probe"] == "READ_REV02_SNAPSHOT_OK"
    assert result["identity_valid"] is True
    assert result["connection_attempted"] is True
    assert result["handshake"]["machine_state_text"] == "READY"
    assert result["reader"]["sequence"] == 42


def test_external_simulator_write_requires_separate_flag(monkeypatch):
    monkeypatch.setattr("app.integrations.plc.external_simulator.settings.plc_external_simulator_enabled", True)
    monkeypatch.setattr("app.integrations.plc.external_simulator.settings.plc_external_simulator_write_enabled", False)
    with pytest.raises(PermissionError, match="escrita"):
        ExternalPlcSimulatorAdapter(config()).write_registers(704, [1], FakeClient())
