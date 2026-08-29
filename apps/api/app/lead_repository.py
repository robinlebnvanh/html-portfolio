"""Lead persistence helpers for service-business demos."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, insert, or_, select, update
from sqlalchemy.orm import Session

from app.sqlalchemy_tables import service_lead_activities, service_leads


LeadStatus = str
VALID_LEAD_STATUSES = {"new", "contacted", "proposal_sent", "booked", "closed"}
VALID_LEAD_CHANNELS = {"form", "phone", "email", "zalo", "facebook", "instagram", "referral"}
VALID_JOB_STAGES = {"awaiting_files", "editing", "review", "revision", "delivered", "paid"}
ADMIN_LEAD_UPDATE_FIELDS = {
    "status",
    "admin_note",
    "follow_up_at",
    "job_stage",
    "quoted_amount",
    "quote_currency",
    "deadline_at",
    "file_url",
    "delivery_url",
    "revision_count",
    "paid_at",
}
NON_NULL_LEAD_UPDATE_FIELDS = {"status", "revision_count"}


def _serialize_time(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _row_to_lead(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "source": row["source"],
        "channel": row.get("channel") or "form",
        "business_name": row["business_name"],
        "customer_name": row["customer_name"],
        "email": row["email"],
        "phone": row.get("phone"),
        "preferred_date": row["preferred_date"],
        "follow_up_at": row.get("follow_up_at"),
        "package_name": row["package_name"],
        "message": row["message"],
        "status": row["status"],
        "admin_note": row["admin_note"],
        "job_stage": row.get("job_stage"),
        "quoted_amount": row.get("quoted_amount"),
        "quote_currency": row.get("quote_currency"),
        "deadline_at": row.get("deadline_at"),
        "file_url": row.get("file_url"),
        "delivery_url": row.get("delivery_url"),
        "revision_count": row.get("revision_count") or 0,
        "paid_at": row.get("paid_at"),
        "created_at": _serialize_time(row["created_at"]),
        "updated_at": _serialize_time(row["updated_at"]),
    }


def create_lead(session: Session, values: dict[str, Any]) -> dict[str, Any]:
    """Create one service-business lead and return the public-safe shape."""

    result = session.execute(
        insert(service_leads).values(
            source=values["source"],
            channel=values.get("channel") or "form",
            business_name=values["business_name"],
            customer_name=values["customer_name"],
            email=values.get("email"),
            phone=values.get("phone"),
            preferred_date=values.get("preferred_date"),
            follow_up_at=values.get("follow_up_at"),
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


def list_leads(
    session: Session,
    status_filter: LeadStatus | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    """Return admin lead list, newest first."""

    query = select(service_leads)
    if status_filter:
        query = query.where(service_leads.c.status == status_filter)
    if search:
        term = f"%{search.lower()}%"
        query = query.where(
            or_(
                service_leads.c.customer_name.ilike(term),
                service_leads.c.business_name.ilike(term),
                service_leads.c.email.ilike(term),
                service_leads.c.phone.ilike(term),
                service_leads.c.package_name.ilike(term),
                service_leads.c.message.ilike(term),
            )
        )
    rows = session.execute(
        query.order_by(desc(service_leads.c.created_at), desc(service_leads.c.id))
    ).mappings().all()
    leads = [_row_to_lead(dict(row)) for row in rows]
    return {"total": len(leads), "leads": leads}


def _row_to_activity(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "lead_id": row["lead_id"],
        "activity_type": row["activity_type"],
        "note": row["note"],
        "created_at": _serialize_time(row["created_at"]),
    }


def list_lead_activities(session: Session, lead_id: int) -> dict[str, Any]:
    """Return activities for one lead, newest first."""

    rows = session.execute(
        select(service_lead_activities)
        .where(service_lead_activities.c.lead_id == lead_id)
        .order_by(desc(service_lead_activities.c.created_at), desc(service_lead_activities.c.id))
    ).mappings().all()
    activities = [_row_to_activity(dict(row)) for row in rows]
    return {"total": len(activities), "activities": activities}


def create_lead_activity(session: Session, lead_id: int, values: dict[str, Any]) -> dict[str, Any] | None:
    """Create one activity note for an existing lead."""

    if get_lead(session, lead_id) is None:
        return None
    result = session.execute(
        insert(service_lead_activities).values(
            lead_id=lead_id,
            activity_type=values.get("activity_type") or "note",
            note=values["note"],
        )
    )
    session.commit()
    row = session.execute(
        select(service_lead_activities).where(
            service_lead_activities.c.id == int(result.inserted_primary_key[0])
        )
    ).mappings().first()
    return _row_to_activity(dict(row)) if row else None


def update_lead(session: Session, lead_id: int, values: dict[str, Any]) -> dict[str, Any] | None:
    """Update admin-owned lead fields."""

    changes = {
        key: value
        for key, value in values.items()
        if key in ADMIN_LEAD_UPDATE_FIELDS
        and (value is not None or key not in NON_NULL_LEAD_UPDATE_FIELDS)
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
