from app.integrations.plc.modbus_supervision import (
    CommunicationHealth,
    SupervisionSnapshot,
    evaluate_supervision,
    get_supervision_diagnostic,
)


def test_starting_blocks_production_until_first_samples():
    out = evaluate_supervision(SupervisionSnapshot(True, now_ms=10_000))
    assert out.health == CommunicationHealth.STARTING
    assert out.may_accept_new_unit is False
    assert out.safe_state is True


def test_healthy_supervision_allows_new_unit():
    out = evaluate_supervision(SupervisionSnapshot(
        True,
        now_ms=10_000,
        last_poll_success_ms=9_900,
        last_pc_heartbeat_write_ms=9_500,
        plc_heartbeat_value=15,
        plc_heartbeat_last_change_ms=9_500,
    ))
    assert out.health == CommunicationHealth.HEALTHY
    assert out.may_accept_new_unit is True
    assert out.safe_state is False


def test_polling_is_due_every_250ms():
    out = evaluate_supervision(SupervisionSnapshot(
        True,
        now_ms=10_000,
        last_poll_success_ms=9_750,
        last_pc_heartbeat_write_ms=9_500,
        plc_heartbeat_value=15,
        plc_heartbeat_last_change_ms=9_500,
    ))
    assert out.poll_due is True


def test_pc_heartbeat_is_due_every_second():
    out = evaluate_supervision(SupervisionSnapshot(
        True,
        now_ms=10_000,
        last_poll_success_ms=9_900,
        last_pc_heartbeat_write_ms=9_000,
        plc_heartbeat_value=15,
        plc_heartbeat_last_change_ms=9_500,
    ))
    assert out.pc_heartbeat_due is True


def test_plc_heartbeat_stale_after_5_seconds_blocks_production():
    out = evaluate_supervision(SupervisionSnapshot(
        True,
        now_ms=10_000,
        last_poll_success_ms=9_900,
        last_pc_heartbeat_write_ms=9_500,
        plc_heartbeat_value=15,
        plc_heartbeat_last_change_ms=5_000,
    ))
    assert out.health == CommunicationHealth.PLC_HEARTBEAT_STALE
    assert out.heartbeat_stale is True
    assert out.may_accept_new_unit is False


def test_transport_retry_is_bounded_and_safe():
    out = evaluate_supervision(SupervisionSnapshot(
        True,
        now_ms=10_000,
        last_poll_success_ms=9_900,
        last_pc_heartbeat_write_ms=9_500,
        plc_heartbeat_value=15,
        plc_heartbeat_last_change_ms=9_500,
        consecutive_transport_failures=1,
    ))
    assert out.health == CommunicationHealth.TRANSPORT_RETRYING
    assert out.transport_retry_allowed is True
    assert out.may_accept_new_unit is False


def test_three_transport_failures_enter_safe_state():
    out = evaluate_supervision(SupervisionSnapshot(
        True,
        now_ms=10_000,
        last_poll_success_ms=9_900,
        last_pc_heartbeat_write_ms=9_500,
        plc_heartbeat_value=15,
        plc_heartbeat_last_change_ms=9_500,
        consecutive_transport_failures=3,
    ))
    assert out.health == CommunicationHealth.DISCONNECTED_SAFE
    assert out.transport_retry_allowed is False
    assert out.requires_reconciliation is True


def test_reconnect_requires_reconciliation_before_writes():
    out = evaluate_supervision(SupervisionSnapshot(True, now_ms=10_000, reconnecting=True))
    assert out.health == CommunicationHealth.RECONNECT_RECONCILE
    assert out.may_accept_new_unit is False
    assert out.requires_reconciliation is True


def test_stage_717_diagnostic_exposes_contract_timings():
    data = get_supervision_diagnostic()
    assert data["stage"] == "7.17"
    assert data["physical_connection_required"] is False
    assert data["polling"]["interval_ms"] == 250
    assert data["pc_heartbeat"]["interval_ms"] == 1000
    assert data["plc_heartbeat"]["stale_after_ms"] == 5000
    assert data["transport"]["retry_attempts"] == 3
    assert data["automatic_operation_target"] is True
