from app.integrations.plc import commissioning_evidence as module


def test_commissioning_evidence_package_is_offline_and_complete(monkeypatch):
    steps = []
    for i in range(1, 13):
        phase = "OFFLINE" if i <= 2 else ("AUTOMATION" if i == 3 else "FACTORY")
        status = "READY" if i <= 2 else ("WAIT_AUTOMATION" if i == 3 else "WAIT_FACTORY")
        steps.append({"code": f"S{i}", "order": i, "title": f"Passo {i}", "phase": phase, "status": status,
                      "evidence": f"Evidência {i}", "requires_machine": phase == "FACTORY"})
    monkeypatch.setattr(module, "get_commissioning_plan", lambda db: {
        "steps": steps, "physical_socket_opened": False, "real_release_allowed": False, "status": "PLAN_READY_OFFLINE"
    })
    monkeypatch.setattr(module, "get_commissioning_readiness", lambda db: {"status": "READY_FOR_OFFLINE_CONTINUATION"})
    monkeypatch.setattr(module, "get_operational_health", lambda db: {"status": "HEALTHY_OFFLINE"})
    monkeypatch.setattr(module, "get_resilience_validation_diagnostic", lambda: {"all_passed": True})

    result = module.get_commissioning_evidence_package(object())
    assert result["stage"] == "7.28"
    assert result["physical_connection_required"] is False
    assert result["physical_socket_opened"] is False
    assert result["evidence_count"] == 12
    assert result["prepared_count"] == 2
    assert result["wait_automation_count"] == 1
    assert result["wait_factory_count"] == 9
    assert "responsavel" in result["required_fields"]
