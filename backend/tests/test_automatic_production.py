from app.integrations.plc.automatic_production import (
    AutomaticProductionSnapshot,
    AutomaticProductionState,
    evaluate_automatic_production,
    get_automatic_production_diagnostic,
)


def test_idle_arms_reader_without_operator():
    d = evaluate_automatic_production(AutomaticProductionSnapshot())
    assert d.state == AutomaticProductionState.WAITING_READER
    assert d.allow_reader is True
    assert d.requires_intervention is False


def test_received_code_requests_automatic_validation():
    d = evaluate_automatic_production(AutomaticProductionSnapshot(reader_has_code=True))
    assert d.state == AutomaticProductionState.VALIDATING_CODE
    assert d.validate_automatically is True


def test_busy_blocks_new_unit():
    d = evaluate_automatic_production(AutomaticProductionSnapshot(reader_has_code=True, scan_valid=True, machine_ready=False, machine_busy=True))
    assert d.state == AutomaticProductionState.WAITING_MACHINE_READY
    assert d.allow_reader is False


def test_transaction_is_persisted_before_write():
    d = evaluate_automatic_production(AutomaticProductionSnapshot(pending_sequence=10))
    assert d.persist_transaction is True
    assert d.write_payload is False
    assert d.write_trigger is False


def test_payload_written_before_trigger():
    d = evaluate_automatic_production(AutomaticProductionSnapshot(pending_sequence=10, transaction_persisted=True))
    assert d.write_payload is True
    d2 = evaluate_automatic_production(AutomaticProductionSnapshot(pending_sequence=10, transaction_persisted=True, payload_written=True))
    assert d2.write_trigger is True


def test_ack_does_not_palletize():
    d = evaluate_automatic_production(AutomaticProductionSnapshot(pending_sequence=10, ack_sequence=10, result_code=1, machine_busy=True))
    assert d.state == AutomaticProductionState.WAITING_CYCLE_COMPLETION
    assert d.finalize_palletized is False


def test_completion_is_only_palletized_authority():
    d = evaluate_automatic_production(AutomaticProductionSnapshot(pending_sequence=10, completed_sequence=10, completion_result=1))
    assert d.state == AutomaticProductionState.FINALIZING_PALLETIZATION
    assert d.finalize_palletized is True
    assert d.allow_reader is False


def test_communication_loss_blocks_reader():
    d = evaluate_automatic_production(AutomaticProductionSnapshot(communication_healthy=False))
    assert d.state == AutomaticProductionState.BLOCKED_COMMUNICATION
    assert d.allow_reader is False


def test_diagnostic_is_offline_and_operatorless_target():
    diag = get_automatic_production_diagnostic()
    assert diag["stage"] == "7.21"
    assert diag["physical_connection_required"] is False
    assert diag["operator_required_normal_flow"] is False
    assert len(diag["scenarios"]) >= 10
