"""Lead persistence helpers for service-business demos."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, insert, select, update
from sqlalchemy.orm import Session

from app.sqlalchemy_tables import service_leads


LeadStatus = str
VALID_LEAD_STATUSES = {"new", "contacted", "proposal_sent", "booked", "closed"}


def _serialize_time(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _row_to_lead(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "source": row["source"],
        "business_name": row["business_name"],
        "customer_name": row["customer_name"],
        "email": row["email"],
        "preferred_date": row["preferred_date"],
        "package_name": row["package_name"],
        "message": row["message"],
        "status": row["status"],
        "admin_note": row["admin_note"],
        "created_at": _serialize_time(row["created_at"]),
        "updated_at": _serialize_time(row["updated_at"]),
    }


def create_lead(session: Session, values: dict[str, Any]) -> dict[str, Any]:
    """Create one service-business lead and return the public-safe shape."""

    result = session.execute(
        insert(service_leads).values(
            source=values["source"],
            business_name=values["business_name"],
            customer_name=values["customer_name"],
            email=values["email"],
            preferred_date=values["preferred_date"],
            package_name=values["package_name"],
            message=values["message"],
        )
    )
    session.commit()
    return get_lead(session, int(result.inserted_primary_key[0]))


def get_lead(session: Session, lead_id: int) -> dict[str, Any] | None:
    """Return one lead by id."""

    row = session.execute(
        select(service_leads).where(service_leads.c.id == lead_id)
    ).mappings().first()
    return _row_to_lead(dict(row)) if row else None


def list_leads(session: Session, status_filter: LeadStatus | None = None) -> dict[str, Any]:
    """Return admin lead list, newest first."""

    query = select(service_leads)
    if status_filter:
        query = query.where(service_leads.c.status == status_filter)
    rows = session.execute(query.order_by(desc(service_leads.c.created_at), desc(service_leads.c.id))).mappings().all()
    leads = [_row_to_lead(dict(row)) for row in rows]
    return {"total": len(leads), "leads": leads}


def update_lead(session: Session, lead_id: int, values: dict[str, Any]) -> dict[str, Any] | None:
    """Update admin-owned lead fields."""

    changes = {
        key: value
        for key, value in values.items()
        if key in {"status", "admin_note"} and value is not None
    }
    if not changes:
        return get_lead(session, lead_id)

    changes["updated_at"] = datetime.now(UTC)
    result = session.execute(
        update(service_leads)
        .where(service_leads.c.id == lead_id)
        .values(**changes)
    )
    if result.rowcount == 0:
        session.rollback()
        return None
    session.commit()
    return get_lead(session, lead_id)
