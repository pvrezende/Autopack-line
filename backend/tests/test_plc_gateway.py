from unittest.mock import Mock
import pytest
from fastapi import HTTPException

from app.integrations.plc import PlcConfirmation, PlcGateway, plc_cycle_state


def _awaiting_sync():
    return {
        "state": "AWAITING_PLC",
        "message": "aguardando",
    }


def test_plc_status_is_simulated_and_ready():
    status = PlcGateway().status()
    assert status["ready"] is True
    assert status["hardware_connected"] is False
    assert status["active_adapter"] == "SIMULATOR_PLC_V1"
    assert status["supported_signals"] == ["PALLETIZE_CONFIRMED", "PALLETIZE_REJECTED"]
    assert "sincronização" in status["message"].lower()


def test_physical_plc_is_blocked_until_hardware_is_defined():
    gateway = PlcGateway()
    with pytest.raises(HTTPException) as exc:
        gateway.process(Mock(), PlcConfirmation(line_id=1, production_unit_id=1, source="PHYSICAL"))
    assert exc.value.status_code == 409


def test_simulated_confirmation_delegates_to_pallet_rule():
    gateway = PlcGateway()
    expected = Mock()
    gateway.inspect_cycle = Mock(return_value=_awaiting_sync())
    gateway.pallet_service.palletize = Mock(return_value=expected)
    db = Mock()
    outcome = gateway.process(db, PlcConfirmation(line_id=2, production_unit_id=9))
    assert outcome.accepted is True
    assert outcome.confirmation_status == "CONFIRMED"
    assert outcome.result is expected
    payload = gateway.pallet_service.palletize.call_args.args[1]
    assert payload.line_id == 2
    assert payload.production_unit_id == 9


def test_plc_rejection_does_not_call_pallet_service_and_keeps_retry_possible():
    gateway = PlcGateway()
    gateway.inspect_cycle = Mock(return_value=_awaiting_sync())
    gateway.pallet_service.palletize = Mock()
    outcome = gateway.process(Mock(), PlcConfirmation(
        line_id=1, production_unit_id=5, signal="PALLETIZE_REJECTED", rejection_reason="Sensor sem confirmação"
    ))
    assert outcome.accepted is False
    assert outcome.confirmation_status == "REJECTED_BY_PLC"
    assert outcome.error_code == "PLC_NACK"
    assert outcome.result is None
    gateway.pallet_service.palletize.assert_not_called()


def test_duplicate_confirmation_is_returned_as_safe_block():
    gateway = PlcGateway()
    gateway.inspect_cycle = Mock(return_value={"state": "PALLETIZED", "message": "já paletizada"})
    outcome = gateway.process(Mock(), PlcConfirmation(line_id=1, production_unit_id=5))
    assert outcome.accepted is False
    assert outcome.confirmation_status == "DUPLICATE_BLOCKED"
    assert outcome.error_code == "PLC_DUPLICATE_CONFIRMATION"
    assert outcome.result is None


def test_nack_after_palletized_is_blocked_as_out_of_sequence():
    gateway = PlcGateway()
    gateway.inspect_cycle = Mock(return_value={"state": "PALLETIZED", "message": "já paletizada"})
    outcome = gateway.process(Mock(), PlcConfirmation(line_id=1, production_unit_id=5, signal="PALLETIZE_REJECTED"))
    assert outcome.accepted is False
    assert outcome.confirmation_status == "OUT_OF_SEQUENCE"
    assert outcome.error_code == "PLC_SEQUENCE_INVALID"


def test_context_mismatch_is_blocked_before_pallet_service():
    gateway = PlcGateway()
    gateway.inspect_cycle = Mock(return_value={"state": "CONTEXT_MISMATCH", "message": "linha incorreta"})
    gateway.pallet_service.palletize = Mock()
    outcome = gateway.process(Mock(), PlcConfirmation(line_id=2, production_unit_id=5))
    assert outcome.confirmation_status == "OUT_OF_SEQUENCE"
    gateway.pallet_service.palletize.assert_not_called()


def test_unknown_signal_is_rejected():
    gateway = PlcGateway()
    with pytest.raises(HTTPException) as exc:
        gateway.process(Mock(), PlcConfirmation(line_id=1, production_unit_id=1, signal="UNKNOWN"))
    assert exc.value.status_code == 422


def test_cycle_inspection_returns_awaiting_for_scanned_unit():
    gateway = PlcGateway()
    unit = Mock(id=5, production_order_id=10, serial_number="SER001", status="SCANNED")
    order = Mock(line_id=1)
    gateway.pallet_service.repository.get_unit = Mock(return_value=unit)
    gateway.pallet_service.repository.get_pallet_item_by_unit = Mock(return_value=None)
    db = Mock()
    db.get = Mock(return_value=order)
    status = gateway.inspect_cycle(db, 1, 5)
    assert status["state"] == "AWAITING_PLC"
    assert status["can_confirm"] is True
    assert status["can_reject"] is True


def test_cycle_inspection_recovers_palletized_state_from_database():
    gateway = PlcGateway()
    unit = Mock(id=5, production_order_id=10, serial_number="SER001", status="PALLETIZED")
    order = Mock(line_id=1)
    item = Mock(pallet_id=20)
    pallet = Mock(id=20, status="OPEN")
    gateway.pallet_service.repository.get_unit = Mock(return_value=unit)
    gateway.pallet_service.repository.get_pallet_item_by_unit = Mock(return_value=item)
    gateway.pallet_service.repository.get_pallet = Mock(return_value=pallet)
    db = Mock()
    db.get = Mock(return_value=order)
    status = gateway.inspect_cycle(db, 1, 5)
    assert status["state"] == "PALLETIZED"
    assert status["pallet"] is pallet
    assert status["can_confirm"] is False


def test_cycle_inspection_detects_wrong_line():
    gateway = PlcGateway()
    unit = Mock(id=5, production_order_id=10, serial_number="SER001", status="SCANNED")
    order = Mock(line_id=7)
    gateway.pallet_service.repository.get_unit = Mock(return_value=unit)
    db = Mock()
    db.get = Mock(return_value=order)
    status = gateway.inspect_cycle(db, 1, 5)
    assert status["state"] == "CONTEXT_MISMATCH"
    assert status["synchronized"] is False


def test_cycle_marks_new_pallet_started():
    result = Mock(sequence_number=1, completed_now=False)
    assert plc_cycle_state(result) == ("NEW_PALLET_STARTED", False, True, "AGUARDAR_PROXIMA_UNIDADE")


def test_cycle_keeps_in_progress_after_first_box():
    result = Mock(sequence_number=2, completed_now=False)
    assert plc_cycle_state(result) == ("PALLET_IN_PROGRESS", False, False, "AGUARDAR_PROXIMA_UNIDADE")


def test_cycle_marks_completed_pallet():
    result = Mock(sequence_number=2, completed_now=True)
    assert plc_cycle_state(result) == ("PALLET_COMPLETED", True, False, "INICIAR_NOVO_PALETE")


def test_latest_cycle_recovers_latest_unit_from_selected_order():
    gateway = PlcGateway()
    order = Mock(id=10, line_id=1)
    unit = Mock(id=99, production_order_id=10, serial_number="SER099", status="SCANNED")
    db = Mock()
    db.get = Mock(return_value=order)
    db.scalar = Mock(return_value=unit)
    gateway.inspect_cycle = Mock(return_value={"state": "AWAITING_PLC", "production_unit_id": 99})

    status = gateway.latest_cycle(db, 1, 10)

    assert status["state"] == "AWAITING_PLC"
    gateway.inspect_cycle.assert_called_once_with(db, 1, 99)


def test_latest_cycle_returns_none_when_order_has_no_units():
    gateway = PlcGateway()
    order = Mock(id=10, line_id=1)
    db = Mock()
    db.get = Mock(return_value=order)
    db.scalar = Mock(return_value=None)

    assert gateway.latest_cycle(db, 1, 10) is None


def test_latest_cycle_rejects_order_from_another_line():
    gateway = PlcGateway()
    db = Mock()
    db.get = Mock(return_value=Mock(id=10, line_id=2))

    with pytest.raises(HTTPException) as exc:
        gateway.latest_cycle(db, 1, 10)

    assert exc.value.status_code == 409


def test_simulator_disconnect_enters_safe_state_and_blocks_confirmation():
    gateway = PlcGateway()
    gateway.inspect_cycle = Mock(return_value=_awaiting_sync())
    gateway.pallet_service.palletize = Mock()
    status = gateway.control_simulator("DISCONNECT")
    assert status["ready"] is False
    assert status["communication_state"] == "DISCONNECTED"
    assert status["safe_state"] is True
    outcome = gateway.process(Mock(), PlcConfirmation(line_id=1, production_unit_id=5))
    assert outcome.accepted is False
    assert outcome.confirmation_status == "COMMUNICATION_UNAVAILABLE"
    assert outcome.error_code == "PLC_DISCONNECTED"
    gateway.pallet_service.palletize.assert_not_called()


def test_simulator_reconnect_restores_processing():
    gateway = PlcGateway()
    gateway.control_simulator("DISCONNECT")
    status = gateway.control_simulator("RECONNECT")
    assert status["ready"] is True
    assert status["communication_state"] == "ONLINE"
    gateway.inspect_cycle = Mock(return_value=_awaiting_sync())
    gateway.pallet_service.palletize = Mock(return_value=Mock())
    outcome = gateway.process(Mock(), PlcConfirmation(line_id=1, production_unit_id=5))
    assert outcome.accepted is True
    assert outcome.confirmation_status == "CONFIRMED"


def test_timeout_next_does_not_palletize_and_is_consumed_once():
    gateway = PlcGateway()
    gateway.inspect_cycle = Mock(return_value=_awaiting_sync())
    gateway.pallet_service.palletize = Mock(return_value=Mock())
    status = gateway.control_simulator("TIMEOUT_NEXT")
    assert status["timeout_next"] is True
    first = gateway.process(Mock(), PlcConfirmation(line_id=1, production_unit_id=5))
    assert first.accepted is False
    assert first.confirmation_status == "TIMEOUT"
    assert first.error_code == "PLC_TIMEOUT"
    gateway.pallet_service.palletize.assert_not_called()
    second = gateway.process(Mock(), PlcConfirmation(line_id=1, production_unit_id=5))
    assert second.accepted is True
    gateway.pallet_service.palletize.assert_called_once()


def test_cannot_arm_timeout_while_disconnected():
    gateway = PlcGateway()
    gateway.control_simulator("DISCONNECT")
    with pytest.raises(HTTPException) as exc:
        gateway.control_simulator("TIMEOUT_NEXT")
    assert exc.value.status_code == 409


def test_retry_control_recovers_after_single_timeout(monkeypatch):
    gateway = PlcGateway()
    monkeypatch.setattr('app.integrations.plc.gateway.settings.plc_retry_interval_seconds', 0)
    monkeypatch.setattr('app.integrations.plc.gateway.settings.plc_retry_max_attempts', 3)
    gateway.inspect_cycle = Mock(return_value=_awaiting_sync())
    expected = Mock()
    gateway.pallet_service.palletize = Mock(return_value=expected)
    gateway.control_simulator('TIMEOUT_NEXT')

    outcome = gateway.process_with_retry(Mock(), PlcConfirmation(line_id=1, production_unit_id=5))

    assert outcome.accepted is True
    assert outcome.confirmation_status == 'CONFIRMED'
    assert outcome.retry_attempts == 2
    assert outcome.retry_max_attempts == 3
    assert outcome.retry_exhausted is False
    assert outcome.last_retry_error == 'PLC_TIMEOUT'
    gateway.pallet_service.palletize.assert_called_once()


def test_retry_cycle_exhaustion_keeps_unit_unpalletized(monkeypatch):
    gateway = PlcGateway()
    monkeypatch.setattr('app.integrations.plc.gateway.settings.plc_retry_interval_seconds', 0)
    monkeypatch.setattr('app.integrations.plc.gateway.settings.plc_retry_max_attempts', 3)
    gateway.inspect_cycle = Mock(return_value=_awaiting_sync())
    gateway.pallet_service.palletize = Mock()
    status = gateway.control_simulator('TIMEOUT_RETRY_CYCLE')
    assert status['timeouts_remaining'] == 3

    outcome = gateway.process_with_retry(Mock(), PlcConfirmation(line_id=1, production_unit_id=5))

    assert outcome.accepted is False
    assert outcome.confirmation_status == 'RETRIES_EXHAUSTED'
    assert outcome.error_code == 'PLC_RETRY_EXHAUSTED'
    assert outcome.retry_attempts == 3
    assert outcome.retry_exhausted is True
    assert outcome.last_retry_error == 'PLC_TIMEOUT'
    gateway.pallet_service.palletize.assert_not_called()
    final_status = gateway.status()
    assert final_status['timeouts_remaining'] == 0
    assert final_status['last_retry_exhausted'] is True


def test_retry_after_exhaustion_can_succeed_without_new_read(monkeypatch):
    gateway = PlcGateway()
    monkeypatch.setattr('app.integrations.plc.gateway.settings.plc_retry_interval_seconds', 0)
    monkeypatch.setattr('app.integrations.plc.gateway.settings.plc_retry_max_attempts', 2)
    gateway.inspect_cycle = Mock(return_value=_awaiting_sync())
    gateway.pallet_service.palletize = Mock(return_value=Mock())
    gateway.control_simulator('TIMEOUT_RETRY_CYCLE')

    first = gateway.process_with_retry(Mock(), PlcConfirmation(line_id=1, production_unit_id=5))
    assert first.confirmation_status == 'RETRIES_EXHAUSTED'

    second = gateway.process_with_retry(Mock(), PlcConfirmation(line_id=1, production_unit_id=5))
    assert second.accepted is True
    assert second.confirmation_status == 'CONFIRMED'
    assert second.retry_attempts == 1
    gateway.pallet_service.palletize.assert_called_once()


def test_disconnected_state_does_not_loop_retries(monkeypatch):
    gateway = PlcGateway()
    monkeypatch.setattr('app.integrations.plc.gateway.settings.plc_retry_interval_seconds', 0)
    monkeypatch.setattr('app.integrations.plc.gateway.settings.plc_retry_max_attempts', 3)
    gateway.inspect_cycle = Mock(return_value=_awaiting_sync())
    gateway.pallet_service.palletize = Mock()
    gateway.control_simulator('DISCONNECT')

    outcome = gateway.process_with_retry(Mock(), PlcConfirmation(line_id=1, production_unit_id=5))

    assert outcome.confirmation_status == 'COMMUNICATION_UNAVAILABLE'
    assert outcome.retry_attempts == 1
    gateway.pallet_service.palletize.assert_not_called()


def test_plc_nack_persists_rejected_state_and_releases_cycle():
    gateway = PlcGateway()
    unit = Mock(id=5, production_order_id=10, serial_number="SER005", status="SCANNED")
    gateway.inspect_cycle = Mock(return_value=_awaiting_sync())
    gateway.pallet_service.repository.get_unit = Mock(return_value=unit)
    gateway.pallet_service.palletize = Mock()
    db = Mock()

    outcome = gateway.process(db, PlcConfirmation(
        line_id=1,
        production_unit_id=5,
        signal="PALLETIZE_REJECTED",
        rejection_reason="NACK de teste",
    ))

    assert outcome.accepted is False
    assert outcome.confirmation_status == "REJECTED_BY_PLC"
    assert outcome.error_code == "PLC_NACK"
    assert unit.status == "PLC_REJECTED"
    db.add.assert_called_once_with(unit)
    db.commit.assert_called_once()
    gateway.pallet_service.palletize.assert_not_called()


def test_cycle_inspection_reports_final_plc_rejection_as_released():
    gateway = PlcGateway()
    unit = Mock(id=5, production_order_id=10, serial_number="SER005", status="PLC_REJECTED")
    order = Mock(line_id=1)
    gateway.pallet_service.repository.get_unit = Mock(return_value=unit)
    gateway.pallet_service.repository.get_pallet_item_by_unit = Mock(return_value=None)
    db = Mock()
    db.get = Mock(return_value=order)

    status = gateway.inspect_cycle(db, 1, 5)

    assert status["state"] == "PLC_REJECTED"
    assert status["can_confirm"] is False
    assert status["can_reject"] is False
    assert status["next_action"] == "AGUARDAR_PROXIMA_UNIDADE"


def test_nack_is_final_and_is_not_reported_as_retryable():
    gateway = PlcGateway()
    unit = Mock(id=5, production_order_id=10, serial_number="SER005", status="SCANNED")
    gateway.inspect_cycle = Mock(return_value=_awaiting_sync())
    gateway.pallet_service.repository.get_unit = Mock(return_value=unit)
    db = Mock()

    outcome = gateway.process_with_retry(db, PlcConfirmation(
        line_id=1,
        production_unit_id=5,
        signal="PALLETIZE_REJECTED",
    ))

    assert outcome.confirmation_status == "REJECTED_BY_PLC"
    assert outcome.retry_attempts == 1
    assert outcome.retry_max_attempts == 1
    assert unit.status == "PLC_REJECTED"
