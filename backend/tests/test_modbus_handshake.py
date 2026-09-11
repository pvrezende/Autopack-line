from app.integrations.plc.modbus_handshake import HandshakeState, MachineSnapshot, evaluate_handshake, get_handshake_diagnostic


def test_ready_machine_can_accept_next_unit():
    out = evaluate_handshake(MachineSnapshot(True, machine_ready=True))
    assert out.state == HandshakeState.IDLE
    assert out.may_send_new_unit is True


def test_busy_machine_blocks_new_unit():
    out = evaluate_handshake(MachineSnapshot(True, machine_ready=True, machine_busy=True))
    assert out.state == HandshakeState.PRECHECK_BLOCKED
    assert out.may_send_new_unit is False


def test_payload_must_be_written_before_trigger():
    out = evaluate_handshake(MachineSnapshot(True, machine_ready=True), pending_sequence=123)
    assert out.state == HandshakeState.READY_TO_WRITE_PAYLOAD
    assert out.may_write_payload is True
    assert out.may_trigger_command is False

    out2 = evaluate_handshake(MachineSnapshot(True, machine_ready=True), pending_sequence=123, payload_written=True)
    assert out2.state == HandshakeState.READY_TO_TRIGGER
    assert out2.may_write_payload is False
    assert out2.may_trigger_command is True


def test_ack_is_not_palletized():
    out = evaluate_handshake(
        MachineSnapshot(True, machine_busy=True, ack_sequence=123, result_code=1),
        pending_sequence=123,
        payload_written=True,
        trigger_written=True,
    )
    assert out.state == HandshakeState.WAITING_CYCLE_COMPLETION
    assert out.may_mark_palletized is False


def test_only_d760_and_d761_placed_can_mark_palletized():
    out = evaluate_handshake(
        MachineSnapshot(True, machine_ready=True, ack_sequence=123, result_code=6, completed_sequence=123, completion_result=1),
        pending_sequence=123,
        payload_written=True,
        trigger_written=True,
    )
    assert out.state == HandshakeState.COMPLETED_PLACED
    assert out.may_mark_palletized is True


def test_physical_cycle_timeout_never_allows_automatic_resend():
    out = evaluate_handshake(
        MachineSnapshot(True, machine_busy=True, ack_sequence=123, result_code=1),
        pending_sequence=123,
        payload_written=True,
        trigger_written=True,
        cycle_elapsed_ms=120000,
    )
    assert out.state == HandshakeState.CYCLE_TIMEOUT_INTERVENTION
    assert out.automatic_resend_allowed is False
    assert out.requires_intervention is True


def test_transport_failure_retries_same_sequence():
    out = evaluate_handshake(
        MachineSnapshot(True, machine_ready=True),
        pending_sequence=123,
        payload_written=True,
        trigger_written=True,
        transport_failed=True,
    )
    assert out.state == HandshakeState.TRANSPORT_RETRY
    assert out.automatic_resend_allowed is True
    assert out.may_send_new_unit is False


def test_reconnect_requires_read_before_write():
    out = evaluate_handshake(MachineSnapshot(True), pending_sequence=123, reconnecting=True)
    assert out.state == HandshakeState.RECONNECT_RECONCILE
    assert out.may_write_payload is False
    assert out.may_trigger_command is False


def test_diagnostic_exposes_offline_automatic_handshake():
    data = get_handshake_diagnostic()
    assert data["stage"] == "7.16"
    assert data["physical_connection_required"] is False
    assert data["automatic_operation_target"] is True
    assert data["ack_is_not_palletized"] is True
    assert data["palletized_rule"] == "D760 == REQUEST_SEQUENCE AND D761 == 1"
