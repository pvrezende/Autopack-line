from __future__ import annotations

from dataclasses import asdict, dataclass

from app.core.config import settings
from app.integrations.plc.modbus_contract import get_modbus_contract


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
        pending_commissioning = list(contract["commissioning_validation"])
        enabled_by_config = bool(settings.plc_physical_enabled)
        write_enabled = bool(settings.plc_write_enabled)
        gates_closed = bool(pending_automation or pending_commissioning)
        activation_allowed = enabled_by_config and bool(settings.plc_read_only_enabled) and not gates_closed
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
            "write_allowed": activation_allowed and write_enabled,
            "socket_opened": False,
            "connection_attempted": False,
            "safe_default": True,
            "pending_automation": pending_automation,
            "pending_commissioning": pending_commissioning,
            "activation_gates": [
                "Ladder Rev.04 compilado no ISPSoft e comparado com o CLP",
                "Offset/endereço Modbus validado no CLP real",
                "Byte order ASCII AB12 validado no CLP real",
                "Porta física do switch e rede 192.168.29.0/24 validadas",
                "Integração EtherNet/IP do SR-1000 validada quando D777 anunciar dados válidos",
                "PLC_PHYSICAL_ENABLED=true somente durante comissionamento autorizado",
            ],
            "message": f"Adaptador Modbus TCP real configurado para {settings.plc_modbus_host}:502 e isolado por feature flag. Nesta etapa nenhum socket é aberto.",
        }


def get_physical_adapter_diagnostic() -> dict:
    return PhysicalModbusAdapter().diagnostic()
