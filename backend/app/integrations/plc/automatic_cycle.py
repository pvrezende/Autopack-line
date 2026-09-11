from __future__ import annotations

from dataclasses import asdict, dataclass
from sqlalchemy.orm import Session

from app.integrations.reader import ReaderGateway, ReaderInput
from app.integrations.plc.gateway import PlcGateway, PlcConfirmation, plc_cycle_state


@dataclass(frozen=True)
class AutomaticOfflineCycleResult:
    accepted: bool
    stage: str
    message: str
    scan_status: str
    unit_id: int | None
    production_order_id: int | None
    plc_confirmation_status: str | None = None
    cycle_state: str | None = None
    next_action: str | None = None
    pallet_code: str | None = None
    pallet_quantity: int | None = None
    pallet_target: int | None = None


def run_automatic_offline_cycle(
    db: Session,
    *,
    line_id: int,
    raw_code: str,
    source: str,
    reader_gateway: ReaderGateway,
    plc_gateway: PlcGateway,
) -> dict:
    """Integra leitor -> validação -> CLP simulado em um único fluxo sem operador.

    ETAPA 7.22: usa somente SIMULATOR/HID_USB e o gateway de CLP simulado.
    Nenhum socket físico é aberto e nenhuma conexão com 192.168.0.2 é feita.
    """
    scan = reader_gateway.ingest(
        db,
        ReaderInput(line_id=line_id, raw_code=raw_code, source=source, code_type='AUTO'),
    )

    if scan.scan.status != 'VALID' or not scan.unit_id:
        return asdict(AutomaticOfflineCycleResult(
            accepted=False,
            stage='READER_VALIDATION',
            message=scan.scan.error_message or f'Leitura finalizada com status {scan.scan.status}.',
            scan_status=scan.scan.status,
            unit_id=scan.unit_id,
            production_order_id=scan.production_order_id,
            next_action='AGUARDAR_NOVO_QR' if scan.scan.status in {'INVALID','REJECTED','DUPLICATE'} else 'REVISAR_LEITURA',
        ))

    outcome = plc_gateway.process_with_retry(
        db,
        PlcConfirmation(
            line_id=line_id,
            production_unit_id=scan.unit_id,
            source='SIMULATOR',
            signal='PALLETIZE_CONFIRMED',
        ),
    )

    cycle_state = None
    next_action = 'AGUARDAR_COMUNICACAO_CLP'
    pallet_code = None
    pallet_quantity = None
    pallet_target = None
    if outcome.result is not None:
        cycle_state, _, _, next_action = plc_cycle_state(outcome.result)
        pallet_code = outcome.result.pallet.pallet_code
        pallet_quantity = outcome.result.pallet.current_quantity
        pallet_target = outcome.result.pallet.target_quantity
    elif outcome.confirmation_status == 'REJECTED_BY_PLC':
        cycle_state, next_action = 'PLC_REJECTED', 'AGUARDAR_PROXIMA_UNIDADE'
    elif outcome.confirmation_status == 'OUT_OF_SEQUENCE':
        cycle_state, next_action = 'OUT_OF_SEQUENCE', 'REVISAR_SEQUENCIA'
    elif outcome.confirmation_status in {'TIMEOUT','COMMUNICATION_UNAVAILABLE','RETRIES_EXHAUSTED'}:
        cycle_state, next_action = 'COMMUNICATION_SAFE_STATE', 'AGUARDAR_COMUNICACAO_CLP'

    return asdict(AutomaticOfflineCycleResult(
        accepted=bool(outcome.accepted and outcome.result is not None),
        stage='SIMULATED_PLC_COMPLETION',
        message=outcome.message,
        scan_status=scan.scan.status,
        unit_id=scan.unit_id,
        production_order_id=scan.production_order_id,
        plc_confirmation_status=outcome.confirmation_status,
        cycle_state=cycle_state,
        next_action=next_action,
        pallet_code=pallet_code,
        pallet_quantity=pallet_quantity,
        pallet_target=pallet_target,
    ))


def get_automatic_cycle_diagnostic() -> dict:
    return {
        'stage': '7.22',
        'status': 'AUTOMATIC_READER_TO_SIMULATOR_READY_OFFLINE',
        'physical_connection_required': False,
        'physical_socket_opened': False,
        'reader_sources': ['HID_USB', 'SIMULATOR'],
        'validation_requires_operator': False,
        'plc_target': 'SIMULATOR_PLC_V1',
        'flow': [
            'RECEBER_QR', 'VALIDAR_AUTOMATICAMENTE', 'CRIAR_UNIDADE',
            'ENVIAR_AO_CLP_SIMULADO', 'AGUARDAR_CONFIRMACAO_SIMULADA',
            'REGISTRAR_RESULTADO', 'LIBERAR_PROXIMO_QR'
        ],
        'safety': [
            'Leitura inválida/rejeitada/duplicada não entra no CLP simulado.',
            'Falha de comunicação mantém a unidade em estado seguro.',
            'A etapa não abre socket físico nem acessa 192.168.0.2.',
        ],
        'message': 'Integração automática leitor → validação → CLP simulado preparada offline; clique manual em Validar leitura deixa de ser necessário quando o modo automático HID estiver ativo.',
    }
