from unittest.mock import Mock

from app.integrations.plc.commissioning_readiness import get_commissioning_readiness


def test_commissioning_readiness_keeps_real_clp_blocked_and_offline_work_allowed():
    db = Mock()
    scalar_result = Mock()
    scalar_result.all.return_value = []
    db.scalars.return_value = scalar_result

    result = get_commissioning_readiness(db)

    assert result["stage"] == "7.26"
    assert result["physical_connection_required"] is False
    assert result["physical_socket_opened"] is False
    assert result["offline_development_allowed"] is True
    assert result["real_commissioning_allowed"] is False
    assert result["checklist_count"] == 7
    assert result["real_blocker_count"] >= 2
    assert result["pending_automation_count"] == 1
    assert result["pending_commissioning_count"] >= 1
    assert any(item["code"] == "LADDER_REV04_ISPSOFT" for item in result["checklist"])
