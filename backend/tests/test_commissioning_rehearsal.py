from app.integrations.plc import commissioning_rehearsal as module


def test_commissioning_rehearsal_is_offline_and_safe(monkeypatch):
    monkeypatch.setattr(module, "get_operational_health", lambda db: {"status": "HEALTHY_OFFLINE"})
    monkeypatch.setattr(module, "get_resilience_validation_diagnostic", lambda: {
        "scenario_count": 10, "passed_count": 10, "failed_count": 0
    })
    monkeypatch.setattr(module, "get_commissioning_readiness", lambda db: {
        "offline_development_allowed": True, "real_commissioning_allowed": False
    })
    monkeypatch.setattr(module, "get_commissioning_plan", lambda db: {
        "status": "PLAN_READY_OFFLINE", "step_count": 3
    })
    monkeypatch.setattr(module, "get_commissioning_evidence_package", lambda db: {
        "status": "EVIDENCE_PACKAGE_READY_OFFLINE",
        "evidence_count": 3,
        "physical_socket_opened": False,
        "items": [
            {"code": "S1", "order": 1, "title": "Baseline", "phase": "OFFLINE", "state": "PREPARED", "expected_evidence": "PASS", "requires_machine": False},
            {"code": "S2", "order": 2, "title": "Ladder", "phase": "AUTOMATION", "state": "WAIT_AUTOMATION", "expected_evidence": "Contrato", "requires_machine": False},
            {"code": "S3", "order": 3, "title": "Teste físico", "phase": "FACTORY", "state": "WAIT_FACTORY", "expected_evidence": "Print/log", "requires_machine": True},
        ],
    })

    result = module.get_commissioning_rehearsal(object())
    assert result["stage"] == "7.29"
    assert result["physical_connection_required"] is False
    assert result["physical_socket_opened"] is False
    assert result["check_count"] == 7
    assert result["fail_count"] == 0
    assert result["status"] == "REHEARSAL_READY_OFFLINE"
    assert result["step_count"] == 3
    assert result["dry_run_ready_count"] == 1
    assert result["wait_automation_count"] == 1
    assert result["wait_factory_count"] == 1
