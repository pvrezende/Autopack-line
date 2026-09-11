from app.integrations.plc.resilience_validation import get_resilience_validation_diagnostic


def test_stage_723_resilience_matrix_passes_offline():
    data = get_resilience_validation_diagnostic()
    assert data["stage"] == "7.23"
    assert data["physical_connection_required"] is False
    assert data["physical_socket_opened"] is False
    assert data["all_passed"] is True
    assert data["failed_count"] == 0
    assert data["passed_count"] == data["scenario_count"]


def test_stage_723_contains_critical_failure_scenarios():
    data = get_resilience_validation_diagnostic()
    names = {item["name"] for item in data["scenarios"]}
    assert {
        "QUEDA_DE_COMUNICACAO",
        "TIMEOUT_TRANSPORTE_EM_RETRY",
        "RETENTATIVAS_ESGOTADAS",
        "HEARTBEAT_CLP_STALE",
        "RECONEXAO_EXIGE_RECONCILIACAO",
        "RESTART_CLP_JA_CONCLUIU",
        "CLP_NAO_CONHECE_PEDIDO_APOS_RETORNO",
        "SEQUENCIA_DIVERGENTE",
        "CLP_REPORTA_SEQUENCIA_DUPLICADA",
        "CICLO_ABORTADO_NAO_PALETIZA",
    }.issubset(names)


def test_stage_723_never_releases_unsafe_scenarios_as_normal_flow():
    data = get_resilience_validation_diagnostic()
    for item in data["scenarios"]:
        assert item["passed"] is True
        assert item["safety_result"] in {
            "NOVAS_UNIDADES_BLOQUEADAS",
            "MESMA_SEQUENCE_PRESERVADA",
            "CONTEXTO_BLOQUEADO",
            "PROXIMO_QR_BLOQUEADO",
        }
