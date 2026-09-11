from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class AutomaticProductionState(str, Enum):
    WAITING_READER = "WAITING_READER"
    VALIDATING_CODE = "VALIDATING_CODE"
    WAITING_MACHINE_READY = "WAITING_MACHINE_READY"
    PERSISTING_TRANSACTION = "PERSISTING_TRANSACTION"
    WRITING_PAYLOAD = "WRITING_PAYLOAD"
    TRIGGERING_REQUEST = "TRIGGERING_REQUEST"
    WAITING_ACK = "WAITING_ACK"
    WAITING_CYCLE_COMPLETION = "WAITING_CYCLE_COMPLETION"
    FINALIZING_PALLETIZATION = "FINALIZING_PALLETIZATION"
    READY_FOR_NEXT_UNIT = "READY_FOR_NEXT_UNIT"
    BLOCKED_COMMUNICATION = "BLOCKED_COMMUNICATION"
    BLOCKED_MACHINE = "BLOCKED_MACHINE"
    BLOCKED_INTERVENTION = "BLOCKED_INTERVENTION"


@dataclass(frozen=True)
class AutomaticProductionSnapshot:
    communication_healthy: bool = True
    machine_ready: bool = True
    machine_busy: bool = False
    machine_fault: bool = False
    maintenance_mode: bool = False
    reader_has_code: bool = False
    scan_valid: bool | None = None
    pending_sequence: int = 0
    transaction_persisted: bool = False
    payload_written: bool = False
    trigger_written: bool = False
    ack_sequence: int = 0
    result_code: int = 0
    completed_sequence: int = 0
    completion_result: int = 0


@dataclass(frozen=True)
class AutomaticProductionDecision:
    state: AutomaticProductionState
    allow_reader: bool
    validate_automatically: bool
    persist_transaction: bool
    write_payload: bool
    write_trigger: bool
    finalize_palletized: bool
    release_next_read: bool
    requires_intervention: bool
    next_action: str
    reason: str


def evaluate_automatic_production(s: AutomaticProductionSnapshot) -> AutomaticProductionDecision:
    seq = int(s.pending_sequence or 0)

    # A conclusão física é autoritativa e sempre vence estados intermediários.
    if seq and s.completed_sequence == seq:
        if s.completion_result == 1:
            return AutomaticProductionDecision(
                AutomaticProductionState.FINALIZING_PALLETIZATION,
                False, False, False, False, False, True, False, False,
                "REGISTRAR_PALLETIZED_E_NEUTRALIZAR_D703",
                "D760 corresponde à REQUEST_SEQUENCE e D761=1: registrar uma única vez e só então liberar a próxima leitura.",
            )
        if s.completion_result in {2, 3}:
            return AutomaticProductionDecision(
                AutomaticProductionState.BLOCKED_INTERVENTION,
                False, False, False, False, False, False, False, s.completion_result == 3,
                "FINALIZAR_SEM_PALETIZAR" if s.completion_result == 2 else "REGISTRAR_ABORTO_E_AGUARDAR_INTERVENCAO",
                "O ciclo terminou sem deposição confirmada; nunca contabilizar como paletizado.",
            )

    if not s.communication_healthy:
        return AutomaticProductionDecision(
            AutomaticProductionState.BLOCKED_COMMUNICATION,
            False, False, False, False, False, False, False, False,
            "AGUARDAR_RECONEXAO_E_RECONCILIAR",
            "Comunicação não confiável bloqueia novas leituras/unidades automaticamente.",
        )

    if s.machine_fault or s.maintenance_mode:
        return AutomaticProductionDecision(
            AutomaticProductionState.BLOCKED_MACHINE,
            False, False, False, False, False, False, False, True,
            "AGUARDAR_MAQUINA_SEGURA",
            "Falha ou manutenção bloqueia o fluxo automático; o dashboard não comanda atuadores.",
        )

    if seq:
        if s.ack_sequence == seq and s.result_code == 1:
            return AutomaticProductionDecision(
                AutomaticProductionState.WAITING_CYCLE_COMPLETION,
                False, False, False, False, False, False, False, False,
                "AGUARDAR_D760_D761",
                "ACK confirma aceite, não paletização. Aguardar a conclusão física da mesma sequência.",
            )
        if s.ack_sequence == seq and s.result_code in {2, 3, 4, 5, 7}:
            return AutomaticProductionDecision(
                AutomaticProductionState.BLOCKED_INTERVENTION,
                False, False, False, False, False, False, False, True,
                "TRATAR_RESULTADO_CLP_SEM_NOVA_SEQUENCIA",
                f"CLP respondeu código {s.result_code}; a unidade não pode avançar automaticamente como paletizada.",
            )
        if s.trigger_written:
            return AutomaticProductionDecision(
                AutomaticProductionState.WAITING_ACK,
                False, False, False, False, False, False, False, False,
                "AGUARDAR_D752_D753",
                "Comando já disparado; manter a mesma REQUEST_SEQUENCE e aguardar o ACK.",
            )
        if s.payload_written:
            return AutomaticProductionDecision(
                AutomaticProductionState.TRIGGERING_REQUEST,
                False, False, False, False, True, False, False, False,
                "GRAVAR_D700_D703_COMMAND_1",
                "Payload já persistido/escrito; disparar o cabeçalho somente depois de D704-D749.",
            )
        if s.transaction_persisted:
            return AutomaticProductionDecision(
                AutomaticProductionState.WRITING_PAYLOAD,
                False, False, False, True, False, False, False, False,
                "GRAVAR_D704_D749",
                "Identidade foi persistida antes da primeira escrita; agora escrever o payload.",
            )
        return AutomaticProductionDecision(
            AutomaticProductionState.PERSISTING_TRANSACTION,
            False, False, True, False, False, False, False, False,
            "PERSISTIR_REQUEST_SEQUENCE_E_PAYLOAD",
            "Uma leitura válida já possui sequência; persistir no MySQL antes de qualquer write Modbus.",
        )

    if not s.reader_has_code:
        return AutomaticProductionDecision(
            AutomaticProductionState.WAITING_READER,
            True, False, False, False, False, False, False, False,
            "AGUARDAR_QR_BARCODE",
            "Sistema saudável e sem unidade pendente: leitor pode permanecer armado sem operador.",
        )

    if s.scan_valid is None:
        return AutomaticProductionDecision(
            AutomaticProductionState.VALIDATING_CODE,
            False, True, False, False, False, False, False, False,
            "VALIDAR_QR_AUTOMATICAMENTE",
            "Código recebido: validação deve ocorrer automaticamente, sem botão de operador.",
        )

    if not s.scan_valid:
        return AutomaticProductionDecision(
            AutomaticProductionState.READY_FOR_NEXT_UNIT,
            True, False, False, False, False, False, True, False,
            "REGISTRAR_REJEICAO_LOGICA_E_LIBERAR_LEITOR",
            "Código inválido/rejeitado pelo AUTOPACKLINE não deve ser enviado ao CLP.",
        )

    if s.machine_busy or not s.machine_ready:
        return AutomaticProductionDecision(
            AutomaticProductionState.WAITING_MACHINE_READY,
            False, False, False, False, False, False, False, False,
            "AGUARDAR_READY_1_BUSY_0",
            "Leitura válida fica retida; nenhuma nova unidade entra enquanto a máquina não estiver pronta.",
        )

    return AutomaticProductionDecision(
        AutomaticProductionState.PERSISTING_TRANSACTION,
        False, False, True, False, False, False, False, False,
        "CRIAR_SEQUENCE_E_PERSISTIR_ANTES_DO_WRITE",
        "Código válido e máquina pronta: criar identidade estável e persistir antes de iniciar o handshake.",
    )


def _scenario(name: str, snapshot: AutomaticProductionSnapshot) -> dict:
    d = evaluate_automatic_production(snapshot)
    return {"name": name, "snapshot": asdict(snapshot), "decision": {**asdict(d), "state": d.state.value}}


def get_automatic_production_diagnostic() -> dict:
    seq = 4321
    scenarios = [
        _scenario("AGUARDANDO_QR", AutomaticProductionSnapshot()),
        _scenario("QR_RECEBIDO_VALIDAR_SOZINHO", AutomaticProductionSnapshot(reader_has_code=True)),
        _scenario("QR_INVALIDO_LIBERA_PROXIMO", AutomaticProductionSnapshot(reader_has_code=True, scan_valid=False)),
        _scenario("VALIDO_MAQUINA_OCUPADA", AutomaticProductionSnapshot(reader_has_code=True, scan_valid=True, machine_busy=True, machine_ready=False)),
        _scenario("VALIDO_PERSISTIR_ANTES_WRITE", AutomaticProductionSnapshot(reader_has_code=True, scan_valid=True, pending_sequence=seq)),
        _scenario("PERSISTIDO_ESCREVER_PAYLOAD", AutomaticProductionSnapshot(pending_sequence=seq, transaction_persisted=True)),
        _scenario("PAYLOAD_DISPARAR_COMMAND", AutomaticProductionSnapshot(pending_sequence=seq, transaction_persisted=True, payload_written=True)),
        _scenario("AGUARDANDO_ACK", AutomaticProductionSnapshot(pending_sequence=seq, transaction_persisted=True, payload_written=True, trigger_written=True)),
        _scenario("ACK_NAO_PALETIZA", AutomaticProductionSnapshot(pending_sequence=seq, ack_sequence=seq, result_code=1, machine_busy=True)),
        _scenario("CONCLUSAO_PALETIZAR", AutomaticProductionSnapshot(pending_sequence=seq, ack_sequence=seq, result_code=6, completed_sequence=seq, completion_result=1)),
        _scenario("SEM_COMUNICACAO", AutomaticProductionSnapshot(communication_healthy=False)),
    ]
    return {
        "stage": "7.21",
        "status": "AUTONOMOUS_PRODUCTION_ENGINE_READY_OFFLINE",
        "physical_connection_required": False,
        "operator_required_normal_flow": False,
        "reader_default_target": "ARMED_WHEN_IDLE",
        "validation_mode_target": "AUTOMATIC_ON_COMPLETE_CODE",
        "automatic_flow": [
            "AGUARDAR_QR", "VALIDAR_AUTOMATICAMENTE", "VERIFICAR_READY_BUSY_FAULT",
            "CRIAR_REQUEST_SEQUENCE", "PERSISTIR_TRANSACAO", "D704-D749", "D700-D703_COMMAND_1",
            "AGUARDAR_D752_D753", "AGUARDAR_D760_D761", "REGISTRAR_RESULTADO", "D703_ZERO", "LIBERAR_PROXIMO_QR",
        ],
        "safety_rules": [
            "Somente uma unidade pendente por linha.",
            "BUSY=1 bloqueia nova unidade.",
            "Comunicação não confiável desarma entrada de novas unidades.",
            "ACK não incrementa produção.",
            "PALLETIZED somente com D760=REQUEST_SEQUENCE e D761=1.",
            "Timeout físico nunca reenvia automaticamente a unidade.",
            "Falha/manutenção exige estado seguro; dashboard não comanda motores, válvulas ou robô.",
        ],
        "states": [x.value for x in AutomaticProductionState],
        "scenarios": scenarios,
        "integration_next_stage": "7.22 liga este motor ao ReaderGateway/HID e ao simulador/transportes sem exigir clique em Validar leitura.",
        "message": "Motor de decisões para produção autônoma preparado offline. Nesta etapa o fluxo sem operador é modelado/testado, mas ainda não é conectado automaticamente ao leitor físico nem ao CLP real.",
    }
