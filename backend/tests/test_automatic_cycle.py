from app.integrations.plc.automatic_cycle import get_automatic_cycle_diagnostic


def test_automatic_cycle_diagnostic_is_offline_and_operatorless():
    d = get_automatic_cycle_diagnostic()
    assert d['status'] == 'AUTOMATIC_READER_TO_SIMULATOR_READY_OFFLINE'
    assert d['physical_connection_required'] is False
    assert d['physical_socket_opened'] is False
    assert d['validation_requires_operator'] is False
    assert d['plc_target'] == 'SIMULATOR_PLC_V1'
    assert d['flow'][0] == 'RECEBER_QR'
    assert d['flow'][-1] == 'LIBERAR_PROXIMO_QR'
