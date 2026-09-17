from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from .commissioning_readiness import get_commissioning_readiness
from .modbus_contract import get_modbus_contract
from .modbus_physical import get_physical_adapter_diagnostic


def _step(
    code: str,
    order: int,
    title: str,
    phase: str,
    status: str,
    detail: str,
    evidence: str,
    requires_machine: bool,
) -> dict[str, Any]:
    return {
        "code": code,
        "order": order,
        "title": title,
        "phase": phase,
        "status": status,
        "detail": detail,
        "evidence": evidence,
        "requires_machine": requires_machine,
    }


def get_commissioning_plan(db: Session) -> dict[str, Any]:
    """ETAPA 7.27 — plano executável de comissionamento, ainda sem conexão física."""
    readiness = get_commissioning_readiness(db)
    contract = get_modbus_contract()
    physical = get_physical_adapter_diagnostic()

    automation_pending = bool(readiness.get("pending_automation_count", 0))
    commissioning_pending = bool(readiness.get("pending_commissioning_count", 0))

    steps = [
        _step(
            "BASELINE_BACKUP", 1, "Congelar baseline do software", "OFFLINE", "READY",
            "Manter ZIP/versão validada, .env de referência e banco preservados antes do comissionamento.",
            "Versão identificada e backup disponível.", False,
        ),
        _step(
            "OFFLINE_HEALTH", 2, "Executar health-check e resiliência", "OFFLINE",
            "READY" if readiness.get("offline_development_allowed") else "BLOCKED",
            "Confirmar saúde offline, matriz de resiliência e ausência de transações pendentes.",
            "Health-check saudável e gate 7.26 sem bloqueio de software.", False,
        ),
        _step(
            "AUTOMATION_CONTRACT", 3, "Compilar e comparar Ladder Rev.04", "AUTOMATION",
            "WAIT_AUTOMATION" if automation_pending else "READY",
            "Abrir a Rev.04 no ISPSoft, compilar, comparar com o CLP e registrar a evidência antes de liberar o modo real.",
            "Confirmação da automação + tabelas aprovadas.", False,
        ),
        _step(
            "NETWORK_SETUP", 4, "Configurar rede isolada de comissionamento", "FACTORY", "WAIT_FACTORY",
            f"Configurar PC e CLP conforme contrato ({contract.get('network_proposal', {}).get('plc_ip', '192.168.29.5')}:502) somente quando a máquina for liberada.",
            "Ping/alcance de rede e porta TCP 502 validados sem alterar ladder.", True,
        ),
        _step(
            "ADDRESS_BYTE_ORDER", 5, "Validar offset Modbus e byte order ASCII", "FACTORY", "WAIT_FACTORY",
            "Ler/escrever bloco de teste controlado e validar o texto AB12 antes de trafegar serial/EAN/OP/modelo reais.",
            "Offset confirmado e AB12 decodificado corretamente.", True,
        ),
        _step(
            "READ_ONLY_STATUS", 6, "Validar leitura D750-D779 e D800-D879", "FACTORY", "WAIT_FACTORY",
            "Iniciar em modo somente leitura: versão do protocolo, heartbeat, estados, falha, palete e receita.",
            "Leituras coerentes por janela de observação sem escrita de comando.", True,
        ),
        _step(
            "HEARTBEAT", 7, "Validar heartbeat e perda de comunicação", "FACTORY", "WAIT_FACTORY",
            "Confirmar D751, detecção de stale em 5 s e bloqueio seguro de novas unidades.",
            "Heartbeat estável e perda simulada detectada conforme contrato.", True,
        ),
        _step(
            "CONTROLLED_HANDSHAKE", 8, "Executar handshake controlado de uma unidade", "FACTORY", "WAIT_FACTORY",
            "Com máquina pronta e autorização da automação, enviar um único REQUEST_SEQUENCE e validar ACK sem contabilizar produção antes de D760/D761.",
            "D752 ecoa a sequência e D753 confirma aceite.", True,
        ),
        _step(
            "PHYSICAL_COMPLETION", 9, "Validar conclusão física e contabilização", "FACTORY", "WAIT_FACTORY",
            "Confirmar que somente D760=REQUEST_SEQUENCE e D761=1 registram a unidade como paletizada.",
            "Uma unidade física concluída e registrada exatamente uma vez.", True,
        ),
        _step(
            "RECONNECT_RESTART", 10, "Testar reconexão e restart com estado pendente", "FACTORY", "WAIT_FACTORY",
            "Executar cenário controlado de perda/retorno e confirmar reconciliação antes de qualquer nova escrita.",
            "Sem duplicidade; mesma REQUEST_SEQUENCE preservada e estado reconciliado.", True,
        ),
        _step(
            "PALLET_FLOW", 11, "Validar capacidade e troca de palete", "FACTORY", "WAIT_FACTORY",
            "Confirmar D759, D758, D755.5/D755.6 e a abertura segura do próximo palete.",
            "Capacidade, completo e troca coerentes com CLP/IHM.", True,
        ),
        _step(
            "AUTONOMOUS_RUN", 12, "Executar lote piloto autônomo", "FACTORY", "WAIT_FACTORY",
            "Após aprovação dos passos anteriores, executar sequência piloto sem operador no fluxo normal e observar rastreabilidade, alarmes e recuperação.",
            "Lote piloto concluído sem intervenção indevida e com rastreabilidade íntegra.", True,
        ),
    ]

    ready_count = sum(1 for step in steps if step["status"] == "READY")
    wait_automation_count = sum(1 for step in steps if step["status"] == "WAIT_AUTOMATION")
    wait_factory_count = sum(1 for step in steps if step["status"] == "WAIT_FACTORY")
    blocked_count = sum(1 for step in steps if step["status"] == "BLOCKED")

    real_release_allowed = (
        readiness.get("real_commissioning_allowed", False)
        and not physical.get("physical_socket_opened", False)
        and not automation_pending
        and not commissioning_pending
    )

    return {
        "stage": "7.27",
        "status": "PLAN_READY_OFFLINE" if blocked_count == 0 else "OFFLINE_ATTENTION",
        "physical_connection_required": False,
        "physical_socket_opened": bool(physical.get("physical_socket_opened", False)),
        "real_release_allowed": real_release_allowed,
        "step_count": len(steps),
        "ready_count": ready_count,
        "wait_automation_count": wait_automation_count,
        "wait_factory_count": wait_factory_count,
        "blocked_count": blocked_count,
        "steps": steps,
        "execution_rule": "Executar em ordem. Não pular compilação Rev.04, leitura somente D750-D779/D800-D879 ou validação AB12/offset.",
        "stop_rule": "Qualquer divergência de sequência, heartbeat, byte order, offset ou estado da máquina interrompe o comissionamento até análise.",
        "next_offline_focus": "Preparar checklist/evidências e continuar software; nenhuma conexão física é necessária nesta etapa.",
        "message": "Plano de comissionamento preparado offline; execução física continua bloqueada até os gates anteriores serem liberados.",
    }
