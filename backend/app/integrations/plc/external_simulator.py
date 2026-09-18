from __future__ import annotations

from dataclasses import asdict, dataclass

from app.core.config import settings

from .modbus_codec import AsciiByteOrder, decode_read_registers
from .modbus_transport import ModbusTcpClient, ModbusTcpTarget, ModbusTransportError
from .rev02_contract import decode_features, decode_reader_snapshot


@dataclass(frozen=True)
class ExternalSimulatorConfig:
    host: str
    port: int
    unit_id: int
    logical_origin: int
    register_base: int
    timeout_ms: int

    def address_for(self, logical_d: int) -> int:
        if not 700 <= logical_d <= 879:
            raise ValueError("registrador lógico fora do contrato D700-D879")
        address = self.register_base + logical_d - self.logical_origin
        if not 0 <= address <= 0xFFFF:
            raise ValueError("mapeamento Modbus resultou em endereço inválido")
        return address


class ExternalPlcSimulatorAdapter:
    adapter = "EXTERNAL_CLP_SIMULATOR_MODBUS_TCP_REV02"

    def __init__(self, config: ExternalSimulatorConfig | None = None) -> None:
        self.config = config or ExternalSimulatorConfig(
            host=settings.plc_external_simulator_host,
            port=settings.plc_external_simulator_port,
            unit_id=settings.plc_external_simulator_unit_id,
            logical_origin=settings.plc_external_simulator_logical_origin,
            register_base=settings.plc_external_simulator_register_base,
            timeout_ms=settings.plc_external_simulator_timeout_ms,
        )

    def _client(self) -> ModbusTcpClient:
        return ModbusTcpClient(ModbusTcpTarget(
            self.config.host, self.config.port, self.config.unit_id, self.config.timeout_ms,
        ))

    def diagnostic(self) -> dict:
        enabled = bool(settings.plc_external_simulator_enabled)
        return {
            "stage": "7.34",
            "status": "EXTERNAL_SIMULATOR_READY" if enabled else "EXTERNAL_SIMULATOR_CONFIGURED_DISABLED",
            "adapter": self.adapter,
            "enabled": enabled,
            "write_enabled": bool(settings.plc_external_simulator_write_enabled),
            "target": asdict(self.config),
            "logical_map": {
                "D700-D749_write": f"holding {self.config.address_for(700)}-{self.config.address_for(749)}",
                "D750-D779_status": f"holding {self.config.address_for(750)}-{self.config.address_for(779)}",
                "D800-D879_reader": f"holding {self.config.address_for(800)}-{self.config.address_for(879)}",
            },
            "physical_plc_enabled": bool(settings.plc_physical_enabled),
            "socket_opened": False,
            "connection_attempted": False,
            "safe_default": True,
            "message": "Perfil externo isolado do CLP físico; conexão ocorre somente por probe explícito.",
        }

    def probe(self, client: ModbusTcpClient | None = None) -> dict:
        if not settings.plc_external_simulator_enabled:
            return {**self.diagnostic(), "connected": False, "probe": "BLOCKED_BY_FEATURE_FLAG"}
        transport = client or self._client()
        try:
            status_values = transport.read_holding_registers(self.config.address_for(750), 30)
            status = {750 + index: value for index, value in enumerate(status_values)}
            expected_identity = {750: 1, 764: 4, 765: 2026, 766: 917, 778: 800, 779: 80}
            mismatches = {address: {"expected": expected, "received": status[address]} for address, expected in expected_identity.items() if status[address] != expected}
            if mismatches:
                raise ValueError(f"identidade Rev.02 incompatível: {mismatches}")
            result = {
                **self.diagnostic(), "connection_attempted": True, "connected": True,
                "probe": "READ_D750_D779_OK", "identity_valid": True,
                "status_registers": status, "handshake": decode_read_registers(status),
                "features": decode_features(status[777]), "reader": None,
            }
            if result["features"]["reader_raw_valid"]:
                reader_values = transport.read_holding_registers(self.config.address_for(800), 80)
                status_after_values = transport.read_holding_registers(self.config.address_for(750), 30)
                reader = {800 + index: value for index, value in enumerate(reader_values)}
                status_after = {750 + index: value for index, value in enumerate(status_after_values)}
                order = AsciiByteOrder(settings.plc_ascii_byte_order)
                result["reader"] = decode_reader_snapshot(status, reader, status_after, order)
                result["probe"] = "READ_REV02_SNAPSHOT_OK"
            return result
        except (ModbusTransportError, ValueError, UnicodeDecodeError) as exc:
            return {**self.diagnostic(), "connection_attempted": True, "connected": False, "probe": "PROBE_ERROR", "message": str(exc)}

    def write_registers(self, logical_start: int, values: list[int], client: ModbusTcpClient | None = None) -> None:
        if not settings.plc_external_simulator_enabled:
            raise PermissionError("simulador externo desabilitado")
        if not settings.plc_external_simulator_write_enabled:
            raise PermissionError("escrita no simulador externo desabilitada")
        if logical_start < 700 or logical_start + len(values) - 1 > 749:
            raise ValueError("escrita permitida somente em D700-D749")
        (client or self._client()).write_holding_registers(self.config.address_for(logical_start), values)


def get_external_simulator_diagnostic() -> dict:
    return ExternalPlcSimulatorAdapter().diagnostic()


def probe_external_simulator() -> dict:
    return ExternalPlcSimulatorAdapter().probe()
