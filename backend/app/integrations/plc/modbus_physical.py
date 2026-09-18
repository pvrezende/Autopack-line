from __future__ import annotations

from dataclasses import asdict, dataclass

from app.core.config import settings
from app.integrations.plc.modbus_codec import AsciiByteOrder, decode_read_registers
from app.integrations.plc.modbus_contract import get_modbus_contract
from app.integrations.plc.modbus_transport import ModbusTcpClient, ModbusTcpTarget, ModbusTransportError
from app.integrations.plc.rev03_contract import decode_features, decode_reader_snapshot


@dataclass(frozen=True)
class PhysicalModbusConfig:
    host: str
    port: int
    unit_id: int
    address_base: int
    ascii_byte_order: str
    read_only_enabled: bool
    write_enabled: bool
    poll_interval_ms: int
    heartbeat_interval_ms: int
    transport_timeout_ms: int
    retry_attempts: int
    retry_interval_ms: int
    ack_timeout_ms: int
    cycle_timeout_ms: int


class PhysicalModbusAdapter:
    """ETAPA 7.20: fronteira física preparada, mas bloqueada por segurança.

    Nenhum socket é criado nesta etapa. A ativação futura exige explicitamente
    PLC_PHYSICAL_ENABLED=true e o fechamento dos gates de automação/comissionamento.
    """

    adapter = "MODBUS_TCP_DELTA_AS228T_A_V1"

    def __init__(self) -> None:
        contract = get_modbus_contract()
        timing = contract["timing"]
        network = contract["network_proposal"]
        self.config = PhysicalModbusConfig(
            host=settings.plc_modbus_host or network["plc_ip"],
            port=settings.plc_modbus_port,
            unit_id=settings.plc_modbus_unit_id,
            address_base=settings.plc_modbus_address_base,
            ascii_byte_order=settings.plc_ascii_byte_order,
            read_only_enabled=settings.plc_read_only_enabled,
            write_enabled=settings.plc_write_enabled,
            poll_interval_ms=timing["poll_interval_ms"],
            heartbeat_interval_ms=timing["heartbeat_interval_ms"],
            transport_timeout_ms=timing["transport_timeout_ms"],
            retry_attempts=timing["transport_retry_attempts"],
            retry_interval_ms=timing["transport_retry_interval_ms"],
            ack_timeout_ms=timing["ack_timeout_ms"],
            cycle_timeout_ms=timing["physical_cycle_timeout_ms"],
        )

    def diagnostic(self) -> dict:
        contract = get_modbus_contract()
        pending_automation = list(contract["pending_automation"])
        commissioning_gates = {
            "ISPsoft_COMPILE": settings.plc_ispsoft_compiled,
            "MODBUS_REGISTER_OFFSET": settings.plc_register_offset_validated,
            "ASCII_BYTE_ORDER_AB12": settings.plc_ascii_byte_order_validated,
            "NETWORK_SWITCH_PORT": settings.plc_network_validated,
            "READER_ETHERNETIP": settings.plc_reader_ethernetip_validated,
            "PHYSICAL_END_TO_END": settings.plc_physical_e2e_authorized,
        }
        pending_commissioning = [name for name, passed in commissioning_gates.items() if not passed]
        enabled_by_config = bool(settings.plc_physical_enabled)
        write_enabled = bool(settings.plc_write_enabled)
        read_gate_names = {"ISPsoft_COMPILE", "MODBUS_REGISTER_OFFSET", "NETWORK_SWITCH_PORT"}
        read_gates_closed = bool(pending_automation or read_gate_names.intersection(pending_commissioning))
        write_gates_closed = bool(pending_automation or pending_commissioning)
        activation_allowed = enabled_by_config and bool(settings.plc_read_only_enabled) and not read_gates_closed
        return {
            "stage": "7.33.1",
            "status": "PHYSICAL_ADAPTER_CONFIGURED_DISABLED",
            "adapter": self.adapter,
            "transport": "MODBUS_TCP",
            "role": "CLIENT",
            "target": asdict(self.config),
            "write_range": contract["write_range"],
            "read_range": contract["read_range"],
            "write_order": ["D704-D749", "D700-D703"],
            "reconnect_read_first": ["D752", "D754", "D757", "D758", "D760", "D761"],
            "physical_enabled_by_config": enabled_by_config,
            "read_only_enabled_by_config": bool(settings.plc_read_only_enabled),
            "write_enabled_by_config": write_enabled,
            "activation_allowed": activation_allowed,
            "write_allowed": activation_allowed and write_enabled and not write_gates_closed,
            "socket_opened": False,
            "connection_attempted": False,
            "safe_default": True,
            "pending_automation": pending_automation,
            "pending_commissioning": pending_commissioning,
            "commissioning_gates": commissioning_gates,
            "activation_gates": [
                "Ladder Rev.06 compilado no ISPSoft e comparado com o CLP",
                "Offset/endereço Modbus validado no CLP real",
                "Byte order ASCII AB12 validado no CLP real",
                "Porta física do switch e rede 192.168.29.0/24 validadas",
                "Integração EtherNet/IP do SR-1000 validada quando D777 anunciar dados válidos",
                "PLC_PHYSICAL_ENABLED=true somente durante comissionamento autorizado",
            ],
            "message": (
                f"Adaptador Modbus TCP real configurado para {settings.plc_modbus_host}:502. "
                + ("A sondagem abre conexão exclusivamente para leitura; escrita permanece bloqueada."
                   if activation_allowed else "Nenhum socket será aberto até a liberação dos requisitos mínimos.")
            ),
        }

    def _address_for(self, logical_d: int) -> int:
        address = logical_d - self.config.address_base
        if not 0 <= address <= 0xFFFF:
            raise ValueError("Endereço físico Modbus inválido")
        return address

    def probe_read_only(self, client: ModbusTcpClient | None = None) -> dict:
        diagnostic = self.diagnostic()
        if not diagnostic["activation_allowed"]:
            return {**diagnostic, "connected": False, "probe": "BLOCKED_BY_COMMISSIONING_GATES"}
        transport = client or ModbusTcpClient(ModbusTcpTarget(
            self.config.host, self.config.port, self.config.unit_id, self.config.transport_timeout_ms,
        ))
        try:
            values = transport.read_holding_registers(self._address_for(750), 30)
            status = {750 + index: value for index, value in enumerate(values)}
            expected = {750: 1, 764: 6, 765: 2026, 766: 918, 777: 15, 778: 800, 779: 89}
            mismatches = {key: {"expected": value, "received": status[key]} for key, value in expected.items() if status[key] != value}
            if mismatches:
                raise ValueError(f"Identidade Rev.06 incompatível: {mismatches}")
            result = {
                **diagnostic,
                "connection_attempted": True,
                "socket_opened": True,
                "connected": True,
                "probe": "READ_D750_D779_OK",
                "identity_valid": True,
                "status_registers": status,
                "handshake": decode_read_registers(status),
                "features": decode_features(status[777]),
                "reader": None,
            }
            if result["features"]["reader_raw_valid"]:
                reader_values = transport.read_holding_registers(self._address_for(800), 89)
                after_values = transport.read_holding_registers(self._address_for(750), 30)
                reader = {800 + index: value for index, value in enumerate(reader_values)}
                after = {750 + index: value for index, value in enumerate(after_values)}
                result["reader"] = decode_reader_snapshot(status, reader, after, AsciiByteOrder(self.config.ascii_byte_order))
                result["probe"] = "READ_REV03_SNAPSHOT_OK"
            return result
        except (ModbusTransportError, ValueError, UnicodeDecodeError) as exc:
            return {**diagnostic, "connection_attempted": True, "connected": False, "probe": "PROBE_ERROR", "message": str(exc)}


def get_physical_adapter_diagnostic() -> dict:
    return PhysicalModbusAdapter().diagnostic()


def probe_physical_adapter_read_only() -> dict:
    return PhysicalModbusAdapter().probe_read_only()
