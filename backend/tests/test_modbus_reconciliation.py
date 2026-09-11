from unittest.mock import Mock

import pytest

from app.integrations.plc.modbus_reconciliation import (
    PersistedRequest,
    PlcReconciliationSnapshot,
    PlcTransactionStore,
    ReconciliationOutcome,
    canonical_payload_hash,
    get_reconciliation_diagnostic,
    reconcile,
    validate_request_sequence,
)


def pending(seq=321):
    return PersistedRequest(seq, "abc")


def test_completion_deposited_is_idempotent_final_confirmation():
    decision = reconcile(pending(), PlcReconciliationSnapshot(321, False, 321, 1))
    assert decision.outcome == ReconciliationOutcome.ALREADY_COMPLETED_DEPOSITED
    assert decision.may_mark_palletized is True
    assert decision.may_write is False
    assert decision.may_create_new_sequence is False


def test_busy_same_ack_only_waits():
    decision = reconcile(pending(), PlcReconciliationSnapshot(321, True, 0, 0))
    assert decision.outcome == ReconciliationOutcome.PLC_STILL_PROCESSING
    assert decision.next_action == "CONTINUAR_AGUARDANDO_D760_D761"
    assert decision.may_write is False


def test_unknown_sequence_resends_same_identity():
    decision = reconcile(pending(), PlcReconciliationSnapshot(0, False, 0, 0))
    assert decision.outcome == ReconciliationOutcome.RESEND_SAME_SEQUENCE
    assert decision.may_write is True
    assert decision.same_request_sequence_required is True
    assert decision.may_create_new_sequence is False


def test_rejected_completion_never_marks_palletized():
    decision = reconcile(pending(), PlcReconciliationSnapshot(321, False, 321, 2))
    assert decision.outcome == ReconciliationOutcome.ALREADY_COMPLETED_REJECTED
    assert decision.may_mark_palletized is False


def test_conflicting_plc_sequence_blocks_automatic_write():
    decision = reconcile(pending(), PlcReconciliationSnapshot(999, False, 999, 1))
    assert decision.outcome == ReconciliationOutcome.CONFLICT_INTERVENTION
    assert decision.requires_operator is True
    assert decision.may_write is False


def test_sequence_zero_and_out_of_range_are_forbidden():
    for value in (0, -1, 65536):
        with pytest.raises(ValueError):
            validate_request_sequence(value)


def test_payload_hash_is_stable_independent_of_key_order():
    assert canonical_payload_hash({"serial":"S1", "ean":"1"}) == canonical_payload_hash({"ean":"1", "serial":"S1"})


def test_store_returns_existing_only_if_identity_matches():
    store = PlcTransactionStore()
    existing = Mock(request_sequence=55, payload_hash=canonical_payload_hash({"serial":"S1"}))
    store.get_by_unit = Mock(return_value=existing)
    db = Mock()
    result = store.persist_before_write(db, line_id=1, production_order_id=2, production_unit_id=3, request_sequence=55, payload={"serial":"S1"})
    assert result is existing
    db.add.assert_not_called()


def test_store_refuses_identity_change_after_restart():
    store = PlcTransactionStore()
    existing = Mock(request_sequence=55, payload_hash=canonical_payload_hash({"serial":"S1"}))
    store.get_by_unit = Mock(return_value=existing)
    with pytest.raises(ValueError):
        store.persist_before_write(Mock(), line_id=1, production_order_id=2, production_unit_id=3, request_sequence=56, payload={"serial":"S1"})


def test_diagnostic_documents_restart_and_read_before_write():
    data = get_reconciliation_diagnostic()
    assert data["stage"] == "7.18"
    assert data["physical_connection_required"] is False
    assert data["persist_before_write"] is True
    assert data["reconnect_read_first"] == ["D752", "D754", "D757", "D758", "D760", "D761"]
    assert len(data["scenarios"]) >= 6
