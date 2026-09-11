from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.plc_transaction import PlcTransaction


@dataclass(frozen=True)
class IndustrialEventDefinition:
    action: str
    category: str
    severity: str
    description: str


EVENT_CATALOG: tuple[IndustrialEventDefinition, ...] = (
    IndustrialEventDefinition("READER_INPUT", "READER", "INFO", "Leitura recebida pela camada de integração."),
    IndustrialEventDefinition("AUTOMATIC_OFFLINE_CYCLE", "PRODUCTION", "INFO", "Ciclo automático leitor → CLP processado."),
    IndustrialEventDefinition("PLC_PALLETIZE_CONFIRMED", "PLC", "INFO", "Confirmação de paletização aceita."),
    IndustrialEventDefinition("PLC_PALLETIZE_REJECTED", "PLC", "WARNING", "CLP rejeitou a unidade."),
    IndustrialEventDefinition("PLC_DUPLICATE_BLOCKED", "SAFETY", "WARNING", "Sequência duplicada bloqueada."),
    IndustrialEventDefinition("PLC_OUT_OF_SEQUENCE", "SAFETY", "ERROR", "Divergência de sequência detectada."),
    IndustrialEventDefinition("PLC_COMMUNICATION_TIMEOUT", "COMMUNICATION", "WARNING", "Timeout de comunicação com o CLP."),
    IndustrialEventDefinition("PLC_COMMUNICATION_UNAVAILABLE", "COMMUNICATION", "ERROR", "Comunicação com o CLP indisponível."),
    IndustrialEventDefinition("PLC_RETRIES_EXHAUSTED", "COMMUNICATION", "ERROR", "Tentativas de transporte esgotadas."),
    IndustrialEventDefinition("PLC_SIMULATOR_CONTROL", "DIAGNOSTIC", "INFO", "Ação executada no simulador para diagnóstico."),
)

_EVENT_INDEX = {item.action: item for item in EVENT_CATALOG}


def classify_industrial_event(action: str) -> dict[str, str]:
    definition = _EVENT_INDEX.get(action)
    if definition:
        return {
            "category": definition.category,
            "severity": definition.severity,
            "description": definition.description,
        }
    return {
        "category": "SYSTEM",
        "severity": "INFO",
        "description": "Evento auditável do AUTOPACKLINE.",
    }


def _event_payload(item: AuditLog) -> dict[str, Any]:
    classification = classify_industrial_event(item.action)
    details = item.details or {}
    return {
        "id": item.id,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "action": item.action,
        "category": classification["category"],
        "severity": classification["severity"],
        "description": classification["description"],
        "username": item.username,
        "entity_type": item.entity_type,
        "entity_id": item.entity_id,
        "line_id": details.get("line_id"),
        "production_order_id": details.get("production_order_id"),
        "production_unit_id": details.get("production_unit_id"),
        "request_sequence": details.get("request_sequence"),
        "cycle_state": details.get("cycle_state"),
        "confirmation_status": details.get("confirmation_status") or details.get("plc_confirmation_status"),
        "error_code": details.get("error_code"),
        "message": details.get("message"),
        "details": details,
    }


def get_industrial_diagnostics(db: Session, *, limit: int = 12) -> dict[str, Any]:
    recent = list(
        db.scalars(
            select(AuditLog)
            .where(AuditLog.action.in_(tuple(_EVENT_INDEX.keys())))
            .order_by(desc(AuditLog.created_at), desc(AuditLog.id))
            .limit(limit)
        ).all()
    )

    pending_transactions = list(
        db.scalars(
            select(PlcTransaction)
            .where(PlcTransaction.resolved_at.is_(None))
            .order_by(desc(PlcTransaction.updated_at), desc(PlcTransaction.id))
            .limit(10)
        ).all()
    )

    events = [_event_payload(item) for item in recent]
    severity_counts = Counter(event["severity"] for event in events)
    category_counts = Counter(event["category"] for event in events)

    pending = [
        {
            "transaction_id": item.id,
            "line_id": item.line_id,
            "production_order_id": item.production_order_id,
            "production_unit_id": item.production_unit_id,
            "request_sequence": item.request_sequence,
            "status": item.status,
            "reconciliation_status": item.reconciliation_status,
            "last_error": item.last_error,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }
        for item in pending_transactions
    ]

    return {
        "stage": "7.24",
        "status": "INDUSTRIAL_DIAGNOSTICS_READY_OFFLINE",
        "physical_connection_required": False,
        "physical_socket_opened": False,
        "persistent_store": "MYSQL_AUDIT_LOGS_AND_PLC_TRANSACTIONS",
        "catalog_size": len(EVENT_CATALOG),
        "recent_event_count": len(events),
        "pending_transaction_count": len(pending),
        "severity_counts": {
            "INFO": severity_counts.get("INFO", 0),
            "WARNING": severity_counts.get("WARNING", 0),
            "ERROR": severity_counts.get("ERROR", 0),
        },
        "category_counts": dict(category_counts),
        "recent_events": events,
        "pending_transactions": pending,
        "retention_note": "Eventos permanecem persistidos no MySQL; a política definitiva de retenção será configurável antes da homologação.",
        "safety": [
            "Diagnóstico não abre socket Modbus físico.",
            "Logs não autorizam reenvio automático de unidade.",
            "REQUEST_SEQUENCE e estado persistido continuam sendo a fonte para reconciliação.",
            "Falhas de comunicação permanecem bloqueantes para novas unidades.",
        ],
        "message": "Logs, auditoria e diagnóstico industrial disponíveis offline para análise de eventos e transações do fluxo automático.",
    }
