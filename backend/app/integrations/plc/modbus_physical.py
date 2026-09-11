from __future__ import annotations

from dataclasses import asdict, dataclass

from app.core.config import settings
from app.integrations.plc.modbus_contract import get_modbus_contract


@dataclass(frozen=True)
class PhysicalModbusConfig:
    host: str
    port: int
    unit_id: int
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
        gates_closed = bool(pending_automation or pending_commissioning)
        activation_allowed = enabled_by_config and not gates_closed
        return {
            "stage": "7.20",
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
            "activation_allowed": activation_allowed,
            "socket_opened": False,
            "connection_attempted": False,
            "safe_default": True,
            "pending_automation": pending_automation,
            "pending_commissioning": pending_commissioning,
            "activation_gates": [
                "Ladder D700-D763 implementado e revisão confirmada",
                "Tabela D754 aprovada",
                "Tabela D756 aprovada",
                "IDs D704/D763 aprovados",
                "Offset/endereço Modbus validado no CLP real",
                "Byte order ASCII AB12 validado no CLP real",
                "PLC_PHYSICAL_ENABLED=true somente durante comissionamento autorizado",
            ],
            "message": "Adaptador Modbus TCP real configurado e isolado por feature flag. Nesta etapa nenhum socket é aberto e nenhuma tentativa é feita contra 192.168.0.2.",
        }


def get_physical_adapter_diagnostic() -> dict:
    return PhysicalModbusAdapter().diagnostic()
