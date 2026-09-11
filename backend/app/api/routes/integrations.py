from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.integrations.reader import ReaderGateway, ReaderInput
from app.models.user import User
from app.schemas.integration_reader import ReaderDiagnosticRequest, ReaderDiagnosticResponse, ReaderIngestRequest, ReaderIngestResponse, ReaderIntegrationStatus
from app.services.audit_service import write_audit


router = APIRouter(prefix="/integrations", tags=["Integrations"])
gateway = ReaderGateway()


@router.get("/reader/status", response_model=ReaderIntegrationStatus)
def reader_status(_: User = Depends(get_current_user)):
    return gateway.status()


@router.post("/reader/diagnose", response_model=ReaderDiagnosticResponse)
def diagnose_reader(
    payload: ReaderDiagnosticRequest,
    _: User = Depends(get_current_user),
):
    return gateway.diagnose(payload.raw_code, payload.source)


@router.post("/reader/ingest", response_model=ReaderIngestResponse)
def ingest_reader(
    payload: ReaderIngestRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    result = gateway.ingest(
        db,
        ReaderInput(
            line_id=payload.line_id,
            raw_code=payload.raw_code,
            source=payload.source,
            code_type=payload.code_type,
        ),
    )
    write_audit(
        db,
        "READER_INPUT",
        actor,
        "SCAN_EVENT",
        result.scan.id,
        {
            "source": payload.source,
            "adapter": gateway.adapter_for(payload.source),
            "status": result.scan.status,
            "line_id": payload.line_id,
        },
    )
    return {
        "source": payload.source,
        "adapter": gateway.adapter_for(payload.source),
        "accepted": True,
        "result": result,
    }


# ETAPA 7.4 — contrato de integração CLP/robô (simulado até definição do hardware real)
from app.integrations.plc import PlcConfirmation, PlcGateway, plc_cycle_state, get_modbus_contract, get_codec_diagnostic, get_handshake_diagnostic, get_supervision_diagnostic, get_reconciliation_diagnostic, get_simulator_diagnostic, get_physical_adapter_diagnostic, get_automatic_production_diagnostic, get_automatic_cycle_diagnostic, run_automatic_offline_cycle, get_resilience_validation_diagnostic, get_industrial_diagnostics, get_operational_health, get_commissioning_readiness, get_commissioning_plan, get_commissioning_evidence_package, get_commissioning_rehearsal
from app.schemas.integration_reader import PlcConfirmRequest, PlcConfirmResponse, PlcIntegrationStatus, PlcCycleStatusResponse, PlcSimulatorControlRequest, PlcAutomaticOfflineCycleRequest, PlcAutomaticOfflineCycleResponse

plc_gateway = PlcGateway()



@router.get("/plc/status", response_model=PlcIntegrationStatus)
def plc_status(_: User = Depends(get_current_user)):
    return plc_gateway.status()


@router.get("/plc/modbus-contract")
def plc_modbus_contract(_: User = Depends(get_current_user)):
    return get_modbus_contract()


@router.get("/plc/modbus-codec")
def plc_modbus_codec(_: User = Depends(get_current_user)):
    return get_codec_diagnostic()


@router.get("/plc/modbus-handshake")
def plc_modbus_handshake(_: User = Depends(get_current_user)):
    return get_handshake_diagnostic()


@router.get("/plc/modbus-supervision")
def plc_modbus_supervision(_: User = Depends(get_current_user)):
    return get_supervision_diagnostic()


@router.get("/plc/modbus-reconciliation")
def plc_modbus_reconciliation(_: User = Depends(get_current_user)):
    return get_reconciliation_diagnostic()


@router.get("/plc/modbus-simulator")
def plc_modbus_simulator(_: User = Depends(get_current_user)):
    return get_simulator_diagnostic()


@router.get("/plc/modbus-physical")
def plc_modbus_physical(_: User = Depends(get_current_user)):
    return get_physical_adapter_diagnostic()


@router.get("/plc/automatic-production")
def plc_automatic_production(_: User = Depends(get_current_user)):
    return get_automatic_production_diagnostic()


@router.get("/plc/automatic-offline-cycle")
def plc_automatic_offline_cycle_diagnostic(_: User = Depends(get_current_user)):
    return get_automatic_cycle_diagnostic()


@router.get("/plc/resilience-validation")
def plc_resilience_validation(_: User = Depends(get_current_user)):
    return get_resilience_validation_diagnostic()


@router.get("/plc/industrial-diagnostics")
def plc_industrial_diagnostics(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_industrial_diagnostics(db)


@router.get("/plc/operational-health")
def plc_operational_health(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_operational_health(db)


@router.get("/plc/commissioning-readiness")
def plc_commissioning_readiness(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_commissioning_readiness(db)


@router.get("/plc/commissioning-plan")
def plc_commissioning_plan(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_commissioning_plan(db)


@router.get("/plc/commissioning-evidence")
def plc_commissioning_evidence(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_commissioning_evidence_package(db)


@router.get("/plc/commissioning-rehearsal")
def plc_commissioning_rehearsal(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_commissioning_rehearsal(db)


@router.post("/plc/automatic-offline-cycle", response_model=PlcAutomaticOfflineCycleResponse)
def plc_automatic_offline_cycle(
    payload: PlcAutomaticOfflineCycleRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    result = run_automatic_offline_cycle(
        db,
        line_id=payload.line_id,
        raw_code=payload.raw_code,
        source=payload.source,
        reader_gateway=gateway,
        plc_gateway=plc_gateway,
    )
    write_audit(
        db,
        "AUTOMATIC_OFFLINE_CYCLE",
        actor,
        "PRODUCTION_UNIT",
        result.get("unit_id"),
        {
            "source": payload.source,
            "line_id": payload.line_id,
            "production_order_id": result.get("production_order_id"),
            "production_unit_id": result.get("unit_id"),
            "accepted": result.get("accepted"),
            "scan_status": result.get("scan_status"),
            "plc_confirmation_status": result.get("plc_confirmation_status"),
            "cycle_state": result.get("cycle_state"),
            "next_action": result.get("next_action"),
        },
    )
    return result




@router.post("/plc/simulator-control", response_model=PlcIntegrationStatus)
def plc_simulator_control(
    payload: PlcSimulatorControlRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    status = plc_gateway.control_simulator(payload.action)
    write_audit(
        db,
        "PLC_SIMULATOR_CONTROL",
        actor,
        "INTEGRATION",
        plc_gateway.simulator_adapter,
        {"action": payload.action, "communication_state": status["communication_state"], "safe_state": status["safe_state"]},
    )
    return status


@router.get("/plc/cycle", response_model=PlcCycleStatusResponse)
def plc_cycle(
    line_id: int,
    production_unit_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return plc_gateway.inspect_cycle(db, line_id, production_unit_id)


@router.get("/plc/latest-cycle", response_model=PlcCycleStatusResponse | None)
def plc_latest_cycle(
    line_id: int,
    production_order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return plc_gateway.latest_cycle(db, line_id, production_order_id)


@router.post("/plc/confirm", response_model=PlcConfirmResponse)
def confirm_plc(
    payload: PlcConfirmRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    outcome = plc_gateway.process_with_retry(
        db,
        PlcConfirmation(
            line_id=payload.line_id,
            production_unit_id=payload.production_unit_id,
            source=payload.source,
            signal=payload.signal,
            rejection_reason=payload.rejection_reason,
        ),
    )

    if outcome.result is not None:
        cycle_state, completed, new_pallet_started, next_action = plc_cycle_state(outcome.result)
        entity_type = "PALLET"
        entity_id = outcome.result.pallet.id
    elif outcome.confirmation_status == "REJECTED_BY_PLC":
        cycle_state, completed, new_pallet_started, next_action = "PLC_REJECTED", False, False, "AGUARDAR_PROXIMA_UNIDADE"
        entity_type = "PRODUCTION_UNIT"
        entity_id = payload.production_unit_id
    elif outcome.confirmation_status == "OUT_OF_SEQUENCE":
        cycle_state, completed, new_pallet_started, next_action = "OUT_OF_SEQUENCE", False, False, "REVISAR_SEQUENCIA"
        entity_type = "PRODUCTION_UNIT"
        entity_id = payload.production_unit_id
    elif outcome.confirmation_status in {"TIMEOUT", "COMMUNICATION_UNAVAILABLE", "RETRIES_EXHAUSTED"}:
        cycle_state, completed, new_pallet_started, next_action = "COMMUNICATION_SAFE_STATE", False, False, "AGUARDAR_COMUNICACAO_CLP"
        entity_type = "PRODUCTION_UNIT"
        entity_id = payload.production_unit_id
    else:
        cycle_state, completed, new_pallet_started, next_action = "DUPLICATE_BLOCKED", False, False, "MANTER_CICLO"
        entity_type = "PRODUCTION_UNIT"
        entity_id = payload.production_unit_id

    audit_action = {
        "CONFIRMED": "PLC_PALLETIZE_CONFIRMED",
        "REJECTED_BY_PLC": "PLC_PALLETIZE_REJECTED",
        "DUPLICATE_BLOCKED": "PLC_DUPLICATE_BLOCKED",
        "OUT_OF_SEQUENCE": "PLC_OUT_OF_SEQUENCE",
        "TIMEOUT": "PLC_COMMUNICATION_TIMEOUT",
        "COMMUNICATION_UNAVAILABLE": "PLC_COMMUNICATION_UNAVAILABLE",
        "RETRIES_EXHAUSTED": "PLC_RETRIES_EXHAUSTED",
    }.get(outcome.confirmation_status, "PLC_SIGNAL_PROCESSED")
    write_audit(
        db,
        audit_action,
        actor,
        entity_type,
        entity_id,
        {
            "source": payload.source,
            "adapter": plc_gateway.simulator_adapter,
            "signal": payload.signal,
            "line_id": payload.line_id,
            "production_unit_id": payload.production_unit_id,
            "confirmation_status": outcome.confirmation_status,
            "error_code": outcome.error_code,
            "message": outcome.message,
            "rejection_reason": payload.rejection_reason,
            "retry_attempts": outcome.retry_attempts,
            "retry_max_attempts": outcome.retry_max_attempts,
            "retry_exhausted": outcome.retry_exhausted,
            "last_retry_error": outcome.last_retry_error,
        },
    )
    return {
        "source": payload.source,
        "adapter": plc_gateway.simulator_adapter,
        "signal": payload.signal,
        "accepted": outcome.accepted,
        "confirmation_status": outcome.confirmation_status,
        "message": outcome.message,
        "error_code": outcome.error_code,
        "cycle_state": cycle_state,
        "pallet_completed": completed,
        "new_pallet_started": new_pallet_started,
        "next_action": next_action,
        "result": outcome.result,
        "retry_attempts": outcome.retry_attempts,
        "retry_max_attempts": outcome.retry_max_attempts,
        "retry_exhausted": outcome.retry_exhausted,
        "last_retry_error": outcome.last_retry_error,
    }

