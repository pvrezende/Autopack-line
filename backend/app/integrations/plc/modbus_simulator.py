from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .modbus_codec import AsciiByteOrder, ModbusPayload, build_write_registers, decode_read_registers
from .rev02_contract import sample_reader_registers


class SimulatorPhase(str, Enum):
    READY = "READY"
    ACCEPTED = "ACCEPTED"
    BUSY = "BUSY"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAULT = "FAULT"


@dataclass
class SimulatorConfig:
    pallet_capacity: int = 2
    active_recipe_id: int = 0
    pallet_sequence: int = 1


class ModbusPlcSimulator:
    """Simulador determinístico do contrato lógico Rev.02.

    Não abre socket, não usa offset Modbus e não representa o ladder real. O objetivo
    é exercitar offline o mesmo mapa de registradores e as mesmas transições que o
    adaptador físico utilizará posteriormente.
    """

    def __init__(self, config: SimulatorConfig | None = None) -> None:
        self.config = config or SimulatorConfig()
        self.pc = {address: 0 for address in range(700, 750)}
        self.plc = {address: 0 for address in range(750, 880)}
        self.phase = SimulatorPhase.READY
        self._last_sequence = 0
        self.reset()

    def reset(self) -> None:
        self.pc.update({address: 0 for address in range(700, 750)})
        self.plc.update({address: 0 for address in range(750, 880)})
        self.plc[750] = 1
        self.plc[751] = 1
        self.plc[754] = 0
        self.plc[755] = 1 << 0  # READY
        self.plc[757] = self.config.pallet_sequence
        self.plc[759] = self.config.pallet_capacity
        self.plc[762] = 1  # ROBOT_PLACE_COMPLETE, conforme contrato atual
        self.plc[763] = self.config.active_recipe_id
        self.plc[764] = 4
        self.plc[765] = 2026
        self.plc[766] = 917
        self.plc[777] = 3
        self.plc[778] = 800
        self.plc[779] = 80
        self.phase = SimulatorPhase.READY
        self._last_sequence = 0

    def heartbeat_tick(self) -> int:
        self.plc[751] = (self.plc[751] + 1) & 0xFFFF
        return self.plc[751]

    def write_payload(self, registers: dict[int, int]) -> None:
        for address in range(704, 750):
            self.pc[address] = registers[address]

    def write_trigger(self, registers: dict[int, int]) -> None:
        for address in range(700, 704):
            self.pc[address] = registers[address]
        self._evaluate_command()

    def submit(self, payload: ModbusPayload, byte_order: AsciiByteOrder = AsciiByteOrder.HIGH_LOW) -> dict:
        registers = build_write_registers(payload, byte_order)
        self.write_payload(registers)
        self.write_trigger(registers)
        return self.snapshot()

    def publish_reader_data(self, registers: dict[int, int] | None = None, *, parsed_fields_valid: bool = True) -> None:
        reader = registers or sample_reader_registers()
        missing = [address for address in range(800, 880) if address not in reader]
        if missing:
            raise ValueError(f"Bloco do leitor incompleto: D{missing[0]} ausente")
        self.plc.update(reader)
        self.plc[770] = reader[800]
        self.plc[771] = reader[846]
        self.plc[769] = reader[801]
        self.plc[777] = 3 | (1 << 2) | (1 << 3)
        if parsed_fields_valid:
            self.plc[777] |= 1 << 4

    def _evaluate_command(self) -> None:
        sequence = self.pc[702]
        command = self.pc[703]
        if command == 0:
            return
        if command == 3:
            self.reset()
            return
        if command == 4:
            return
        if sequence == 0 or self.pc[700] != 1:
            self.plc[753] = 2
            return
        retest_authorized = bool(self.pc[705] & (1 << 4))
        if retest_authorized != (self.pc[749] != 0):
            self.plc[752] = sequence
            self.plc[753] = 2
            return
        if command == 2:
            self.plc[752] = sequence
            self.plc[753] = 1
            self.plc[760] = sequence
            self.plc[761] = 2
            self.plc[755] = 1 << 0
            self.phase = SimulatorPhase.REJECTED
            return
        if command != 1:
            self.plc[753] = 2
            return
        if self.plc[755] & (1 << 2):
            self.plc[752] = sequence
            self.plc[753] = 5
            return
        if self.plc[755] & (1 << 1):
            self.plc[752] = sequence
            self.plc[753] = 4
            return
        if sequence == self._last_sequence and sequence != 0:
            self.plc[752] = sequence
            self.plc[753] = 3
            return
        self._last_sequence = sequence
        self.plc[752] = sequence
        self.plc[753] = 1
        self.plc[755] = (1 << 1) | (1 << 3)  # BUSY + REQUEST_ACCEPTED
        self.phase = SimulatorPhase.ACCEPTED

    def start_cycle(self) -> None:
        if self.plc[753] != 1 or self.plc[752] == 0:
            raise ValueError("Nenhuma solicitação aceita para iniciar ciclo")
        self.plc[755] = 1 << 1
        self.phase = SimulatorPhase.BUSY

    def complete_cycle(self, deposited: bool = True) -> None:
        sequence = self.plc[752]
        if sequence == 0:
            raise ValueError("Nenhuma sequência ativa")
        self.plc[760] = sequence
        self.plc[761] = 1 if deposited else 3
        if deposited:
            self.plc[758] = min(self.plc[758] + 1, self.plc[759])
            flags = (1 << 0) | (1 << 4)  # READY + UNIT_PLACED
            if self.plc[758] >= self.plc[759] > 0:
                flags |= 1 << 5
            self.plc[755] = flags
            self.plc[753] = 6
            self.phase = SimulatorPhase.COMPLETED
        else:
            self.plc[755] = 1 << 0
            self.plc[753] = 7
            self.phase = SimulatorPhase.REJECTED

    def neutralize_command(self) -> None:
        self.pc[703] = 0
        if self.phase in {SimulatorPhase.COMPLETED, SimulatorPhase.REJECTED}:
            self.plc[755] &= ~((1 << 3) | (1 << 4))
            if not (self.plc[755] & (1 << 5)):
                self.plc[755] |= 1 << 0
            self.phase = SimulatorPhase.READY

    def set_fault(self, code: int = 1) -> None:
        self.plc[756] = code
        self.plc[755] = 1 << 2
        self.plc[753] = 5
        self.phase = SimulatorPhase.FAULT

    def clear_fault(self) -> None:
        self.plc[756] = 0
        self.plc[753] = 0
        self.plc[755] = 1 << 0
        self.phase = SimulatorPhase.READY

    def snapshot(self) -> dict:
        return {"phase": self.phase.value, "write_registers": dict(self.pc), "read_registers": dict(self.plc), "decoded": decode_read_registers(self.plc)}


def get_simulator_diagnostic() -> dict:
    sim = ModbusPlcSimulator(SimulatorConfig(pallet_capacity=2, active_recipe_id=0, pallet_sequence=10))
    payload = ModbusPayload(1, 25, 1234, 1, 0, "AB12", "7908412552656", "000001275033", "HJFE12C2CG")
    accepted = sim.submit(payload)
    sim.start_cycle()
    busy = sim.snapshot()
    sim.complete_cycle(deposited=True)
    completed = sim.snapshot()
    return {
        "stage": "7.19",
        "status": "FULL_REGISTER_SIMULATOR_READY_OFFLINE",
        "physical_connection_required": False,
        "adapter": "SIMULATOR_MODBUS_REV02_V2",
        "logical_register_range": "D700-D779 + D800-D879",
        "socket_opened": False,
        "modbus_offset_applied": False,
        "byte_order_for_test_only": "HIGH_LOW",
        "capabilities": [
            "D700-D749 em memória com escrita em duas fases",
            "D750-D779 em memória com identidade Rev.04 e diagnóstico do leitor",
            "D800-D879 em memória para simulação do bloco SR-1000",
            "ACK D752/D753", "READY/BUSY/FAULT e bits D755", "heartbeat D751",
            "conclusão D760/D761", "palete D757-D759", "rejeição e aborto",
        ],
        "sample_flow": {
            "request_sequence": 1234,
            "after_command": {"phase": accepted["phase"], "ack_sequence": accepted["decoded"]["ack_sequence"], "result": accepted["decoded"]["result_name"]},
            "during_cycle": {"phase": busy["phase"], "busy": busy["decoded"]["machine_flags"]["machine_busy"]},
            "after_completion": {"phase": completed["phase"], "completed_sequence": completed["decoded"]["completed_sequence"], "completion": completed["decoded"]["completion_result_name"], "boxes_on_pallet": completed["decoded"]["boxes_on_pallet"]},
        },
        "pending_commissioning": ["ASCII_BYTE_ORDER_AB12", "MODBUS_REGISTER_OFFSET", "ISPsoft_COMPILE", "PHYSICAL_END_TO_END"],
        "pending_automation": [],
        "message": "Simulador Rev.02 dos blocos D700-D779 e D800-D879 preparado offline; nenhuma conexão com a máquina real é aberta nesta etapa.",
    }
