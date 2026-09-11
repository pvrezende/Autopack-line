from unittest.mock import Mock

from app.integrations.plc.operational_health import get_operational_health


def test_operational_health_is_safe_offline():
    db = Mock()
    scalar_result = Mock()
    scalar_result.all.return_value = []
    db.scalars.return_value = scalar_result

    result = get_operational_health(db)

    assert result["stage"] == "7.25"
    assert result["physical_socket_opened"] is False
    assert result["real_machine_release_allowed"] is False
    assert result["check_count"] == 7
    assert result["status"] == "HEALTHY_OFFLINE"
    assert result["blocking_count"] == 0
    assert any(item["name"] == "BACKEND_API" for item in result["checks"])
    assert any(item["name"] == "MYSQL" for item in result["checks"])
    db.execute.assert_called_once()
