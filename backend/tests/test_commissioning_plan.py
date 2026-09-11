from app.integrations.plc.commissioning_plan import get_commissioning_plan


def test_commissioning_plan_is_offline_and_ordered(monkeypatch):
    monkeypatch.setattr(
        "app.integrations.plc.commissioning_plan.get_commissioning_readiness",
        lambda db: {
            "offline_development_allowed": True,
            "real_commissioning_allowed": False,
            "pending_automation_count": 3,
            "pending_commissioning_count": 4,
        },
    )
    monkeypatch.setattr(
        "app.integrations.plc.commissioning_plan.get_modbus_contract",
        lambda: {"connection": {"plc_ip": "192.168.0.2"}},
    )
    monkeypatch.setattr(
        "app.integrations.plc.commissioning_plan.get_physical_adapter_diagnostic",
        lambda: {"physical_socket_opened": False},
    )

    result = get_commissioning_plan(None)
    assert result["stage"] == "7.27"
    assert result["status"] == "PLAN_READY_OFFLINE"
    assert result["physical_connection_required"] is False
    assert result["physical_socket_opened"] is False
    assert result["real_release_allowed"] is False
    assert result["step_count"] == 12
    assert [step["order"] for step in result["steps"]] == list(range(1, 13))
    assert result["steps"][2]["status"] == "WAIT_AUTOMATION"
    assert result["steps"][3]["status"] == "WAIT_FACTORY"
    assert "AB12" in result["steps"][4]["detail"]
    assert "D750-D763" in result["steps"][5]["title"]


def test_plan_never_claims_real_release_with_socket_open(monkeypatch):
    monkeypatch.setattr(
        "app.integrations.plc.commissioning_plan.get_commissioning_readiness",
        lambda db: {
            "offline_development_allowed": True,
            "real_commissioning_allowed": True,
            "pending_automation_count": 0,
            "pending_commissioning_count": 0,
        },
    )
    monkeypatch.setattr(
        "app.integrations.plc.commissioning_plan.get_modbus_contract",
        lambda: {"connection": {"plc_ip": "192.168.0.2"}},
    )
    monkeypatch.setattr(
        "app.integrations.plc.commissioning_plan.get_physical_adapter_diagnostic",
        lambda: {"physical_socket_opened": True},
    )

    result = get_commissioning_plan(None)
    assert result["real_release_allowed"] is False
