from app.integrations.plc.rev02_contract import decode_features, decode_reader_block, get_rev02_diagnostic, sample_reader_registers


def test_rev02_identity_and_safe_defaults():
    result = get_rev02_diagnostic()
    assert result["stage"] == "7.33"
    assert result["identity_probe"] == {"D750": 1, "D764": 4, "D765": 2026, "D766": 917}
    assert result["connection"]["host"] == "192.168.29.5"
    assert result["connection"]["socket_opened"] is False
    assert result["connection"]["physical_enabled"] is False
    assert result["ranges"]["reader"] == "D800-D879"


def test_initial_feature_flags_only_dashboard_and_retest():
    flags = decode_features(3)
    assert flags["dashboard_d700_d779"] is True
    assert flags["retest"] is True
    assert flags["reader_status_valid"] is False
    assert flags["reader_raw_valid"] is False
    assert flags["reader_parsed_fields_valid"] is False


def test_reader_block_high_low_decode():
    decoded = decode_reader_block(sample_reader_registers())
    assert decoded["result_name"] == "GOOD"
    assert decoded["serial"] == "ARC881493129837"
    assert decoded["production_order"] == "000001275033"
    assert decoded["raw"].startswith("AB12;")


def test_reader_block_rejects_invalid_length():
    registers = sample_reader_registers()
    registers[803] = 33
    try:
        decode_reader_block(registers)
        assert False, "deveria rejeitar comprimento inválido"
    except ValueError as exc:
        assert "Comprimento inválido" in str(exc)
