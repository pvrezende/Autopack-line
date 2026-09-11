from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

ContractStatus = Literal["DEFINED", "PENDING_AUTOMATION", "COMMISSIONING_ONLY"]
Direction = Literal["PC_TO_PLC", "PLC_TO_PC"]


@dataclass(frozen=True)
class RegisterDefinition:
    address: str
    name: str
    data_type: str
    direction: Direction
    description: str
    status: ContractStatus = "DEFINED"


WRITE_REGISTERS: tuple[RegisterDefinition, ...] = (
    RegisterDefinition("D700", "AP_PROTOCOL_VERSION", "UINT16", "PC_TO_PLC", "Versão do protocolo. Valor definido: 1."),
    RegisterDefinition("D701", "AP_PC_HEARTBEAT", "UINT16", "PC_TO_PLC", "Contador incrementado pelo AUTOPACKLINE a cada 1 segundo."),
    RegisterDefinition("D702", "AP_REQUEST_SEQUENCE", "UINT16", "PC_TO_PLC", "Sequência única, não nula, persistente para a mesma unidade."),
    RegisterDefinition("D703", "AP_COMMAND", "UINT16", "PC_TO_PLC", "0 neutro; 1 solicitar ciclo; 2 unidade rejeitada pelo PC; 3 resetar interface; 4 solicitar sincronização."),
    RegisterDefinition("D704", "AP_RECIPE_ID", "UINT16", "PC_TO_PLC", "Código numérico da receita.", "PENDING_AUTOMATION"),
    RegisterDefinition("D705", "AP_PAYLOAD_FLAGS", "WORD", "PC_TO_PLC", "bit0 serial; bit1 EAN; bit2 OP; bit3 modelo."),
    RegisterDefinition("D706", "AP_SERIAL_LENGTH", "UINT16", "PC_TO_PLC", "Comprimento do serial, 0 a 32."),
    RegisterDefinition("D707-D722", "AP_SERIAL", "ASCII[32]", "PC_TO_PLC", "Serial, 2 caracteres por registrador; byte order será validado no comissionamento com AB12.", "COMMISSIONING_ONLY"),
    RegisterDefinition("D723", "AP_EAN_LENGTH", "UINT16", "PC_TO_PLC", "Comprimento do EAN, 0 a 14."),
    RegisterDefinition("D724-D730", "AP_EAN", "ASCII[14]", "PC_TO_PLC", "EAN, 2 caracteres por registrador; byte order será validado no comissionamento.", "COMMISSIONING_ONLY"),
    RegisterDefinition("D731", "AP_OP_LENGTH", "UINT16", "PC_TO_PLC", "Comprimento da ordem de produção, 0 a 16."),
    RegisterDefinition("D732-D739", "AP_OP", "ASCII[16]", "PC_TO_PLC", "Ordem de produção em ASCII sem acentos."),
    RegisterDefinition("D740", "AP_MODEL_LENGTH", "UINT16", "PC_TO_PLC", "Comprimento do modelo, 0 a 16."),
    RegisterDefinition("D741-D748", "AP_MODEL", "ASCII[16]", "PC_TO_PLC", "Código do modelo em ASCII sem acentos."),
    RegisterDefinition("D749", "AP_PAYLOAD_RESERVED", "UINT16", "PC_TO_PLC", "Reservado; AUTOPACKLINE deve gravar zero."),
)

READ_REGISTERS: tuple[RegisterDefinition, ...] = (
    RegisterDefinition("D750", "AP_PLC_PROTOCOL_VERSION", "UINT16", "PLC_TO_PC", "Valor 1 quando o contrato estiver disponível no ladder."),
    RegisterDefinition("D751", "AP_PLC_HEARTBEAT", "UINT16", "PLC_TO_PC", "Contador incrementado pelo CLP a cada 1 segundo."),
    RegisterDefinition("D752", "AP_ACK_SEQUENCE", "UINT16", "PLC_TO_PC", "Eco da sequência recebida."),
    RegisterDefinition("D753", "AP_RESULT_CODE", "UINT16", "PLC_TO_PC", "0 sem resposta; 1 aceita; 2 dados inválidos; 3 sequência duplicada; 4 ocupada; 5 falha; 6 ciclo concluído; 7 abortado."),
    RegisterDefinition("D754", "AP_MACHINE_STATE", "UINT16", "PLC_TO_PC", "Estado operacional resumido; tabela numérica ainda pendente da automação.", "PENDING_AUTOMATION"),
    RegisterDefinition("D755.0-D755.8", "AP_MACHINE_FLAGS", "WORD/BITS", "PLC_TO_PC", "READY, BUSY, FAULT, REQUEST_ACCEPTED, UNIT_PLACED, PALLET_COMPLETE, PALLET_CHANGE_ACTIVE, MAINTENANCE_MODE, PC_COMM_STALE."),
    RegisterDefinition("D756", "AP_ACTIVE_FAULT_CODE", "UINT16", "PLC_TO_PC", "Código de falha ativo; tabela código/texto ainda pendente da automação.", "PENDING_AUTOMATION"),
    RegisterDefinition("D757", "AP_PALLET_SEQUENCE", "UINT16", "PLC_TO_PC", "Identificador do palete atual."),
    RegisterDefinition("D758", "AP_BOXES_ON_PALLET", "UINT16", "PLC_TO_PC", "Quantidade confirmada no palete."),
    RegisterDefinition("D759", "AP_PALLET_CAPACITY", "UINT16", "PLC_TO_PC", "Capacidade da receita ativa; no modo real o CLP/IHM é a autoridade."),
    RegisterDefinition("D760", "AP_COMPLETED_SEQUENCE", "UINT16", "PLC_TO_PC", "Sequência da última unidade concluída."),
    RegisterDefinition("D761", "AP_COMPLETION_RESULT", "UINT16", "PLC_TO_PC", "0 nenhuma; 1 depositada; 2 rejeitada; 3 abortada."),
    RegisterDefinition("D762", "AP_PLACE_CONFIRM_SOURCE", "UINT16", "PLC_TO_PC", "0 nenhuma; 1 robô; 2 sensor/visão independente."),
    RegisterDefinition("D763", "AP_ACTIVE_RECIPE_ID", "UINT16", "PLC_TO_PC", "Receita ativa no CLP/robô; relação de IDs ainda pendente da automação.", "PENDING_AUTOMATION"),
)


def get_modbus_contract() -> dict:
    pending = sorted({item.name for item in (*WRITE_REGISTERS, *READ_REGISTERS) if item.status == "PENDING_AUTOMATION"})
    commissioning = sorted({item.name for item in (*WRITE_REGISTERS, *READ_REGISTERS) if item.status == "COMMISSIONING_ONLY"})
    return {
        "stage": "7.14",
        "status": "PROPOSAL_NOT_IMPLEMENTED_IN_LADDER",
        "plc": {
            "manufacturer": "Delta",
            "model": "AS228T-A",
            "role": "SERVER",
            "protocol": "MODBUS_TCP",
            "tcp_port": 502,
        },
        "network_proposal": {
            "plc_ip": "192.168.0.2",
            "pc_ip": "192.168.0.10",
            "netmask": "255.255.255.0",
            "gateway": None,
            "topology": "PC e CLP conectados ao switch da máquina",
        },
        "timing": {
            "poll_interval_ms": 250,
            "heartbeat_interval_ms": 1000,
            "transport_timeout_ms": 1000,
            "transport_retry_attempts": 3,
            "transport_retry_interval_ms": 1000,
            "ack_timeout_ms": 2000,
            "physical_cycle_timeout_ms": 120000,
            "heartbeat_stale_ms": 5000,
            "physical_cycle_timeout_allows_automatic_resend": False,
        },
        "write_range": "D700-D749",
        "read_range": "D750-D763",
        "write_registers": [asdict(item) for item in WRITE_REGISTERS],
        "read_registers": [asdict(item) for item in READ_REGISTERS],
        "normal_sequence": [
            "Incrementar D701 a cada 1 segundo.",
            "Ler D750-D763 a cada 250 ms.",
            "Antes do envio confirmar READY=1, BUSY=0 e FAULT=0.",
            "Validar QR/barcode e obter REQUEST_SEQUENCE única e persistente.",
            "Gravar primeiro D704-D749.",
            "Gravar D700-D703 por último com COMMAND=1.",
            "Aguardar D752 igual à REQUEST_SEQUENCE.",
            "D753=1 confirma apenas o aceite pelo CLP.",
            "Aguardar D760 igual à REQUEST_SEQUENCE e D761=1.",
            "Somente então registrar PALLETIZED.",
            "Retornar D703 para zero e liberar a próxima leitura.",
        ],
        "reconnect_rules": [
            "Bloquear novas unidades durante queda de comunicação.",
            "Persistir último pedido e último resultado confirmado.",
            "Após reconexão ler D752, D754, D757, D758, D760 e D761 antes de escrever.",
            "Se D760=sequência pendente e D761=1, registrar uma única vez.",
            "Se D752=sequência pendente e BUSY=1, continuar aguardando.",
            "Se o CLP não conhecer a sequência, reenviar o mesmo pacote com a mesma REQUEST_SEQUENCE.",
        ],
        "authority_rules": {
            "machine_motion_authority": "PLC",
            "pallet_capacity_authority": "PLC_IHM_RECIPE",
            "palletized_confirmation": "D760 == REQUEST_SEQUENCE AND D761 == 1",
            "current_physical_confirmation_source": "ROBOT_PLACE_COMPLETE",
            "independent_box_presence_confirmation_available": False,
        },
        "pending_automation": pending,
        "commissioning_validation": commissioning + ["MODBUS_REGISTER_OFFSET", "LADDER_REVISION"],
        "message": "Contrato real formalizado no software. O adaptador físico permanece desabilitado até o ladder D700-D763 existir e os itens pendentes serem fechados.",
    }
