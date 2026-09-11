from app.integrations.plc.industrial_diagnostics import EVENT_CATALOG, classify_industrial_event


def test_industrial_event_catalog_has_operational_coverage():
    actions = {item.action for item in EVENT_CATALOG}
    assert "AUTOMATIC_OFFLINE_CYCLE" in actions
    assert "PLC_COMMUNICATION_TIMEOUT" in actions
    assert "PLC_RETRIES_EXHAUSTED" in actions
    assert "PLC_DUPLICATE_BLOCKED" in actions
    assert len(actions) >= 10


def test_critical_industrial_events_are_not_classified_as_info():
    assert classify_industrial_event("PLC_COMMUNICATION_UNAVAILABLE")["severity"] == "ERROR"
    assert classify_industrial_event("PLC_OUT_OF_SEQUENCE")["severity"] == "ERROR"
    assert classify_industrial_event("PLC_COMMUNICATION_TIMEOUT")["severity"] == "WARNING"
