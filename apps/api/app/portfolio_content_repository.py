"""Portfolio content persistence helpers for the personal site."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, insert, select, update
from sqlalchemy.orm import Session

from app.sqlalchemy_tables import portfolio_content


DEFAULT_PORTFOLIO_CONTENT: dict[str, Any] = {
    "hero_eyebrow": "Senior software engineer / Product studio",
    "hero_title": "Building full-stack tools people can actually use.",
    "hero_intro": (
        "I turn service-business workflows into reliable web products: booking "
        "flows, operating dashboards, admin tools, automation, and clear case "
        "studies that prove the work."
    ),
    "hero_location": "Vietnam based / Remote-ready",
    "hero_experience": "10+ years shipping software",
    "about_title": "Senior delivery mindset, hands-on product execution.",
    "about_body": [
        "I am Robin, a software engineer and delivery lead with over a decade of experience moving work from unclear business need to stable release.",
        "My current portfolio is intentionally shaped as a product studio: every demo must identify a customer, a workflow pain, a usable MVP, and a credible path to paid implementation.",
    ],
    "github_url": "https://github.com/robinlebnvanh",
    "studio_title": "Portfolio projects designed to become sellable offers.",
    "studio_intro": (
        "The studio direction is practical: small tools for businesses that sell "
        "appointments, services, creative packages, or recurring client work."
    ),
    "offers": [
        {
            "kicker": "Offer 01",
            "title": "Booking-ready service website",
            "description": "Landing page, service menu, enquiry flow, availability signal, analytics, and conversion-focused content for salons, studios, and local experts.",
        },
        {
            "kicker": "Offer 02",
            "title": "Lightweight operations dashboard",
            "description": "Admin UI for leads, appointments, notes, simple revenue tracking, and follow-up reminders without forcing a small team into a heavy CRM.",
        },
        {
            "kicker": "Offer 03",
            "title": "Automation starter kit",
            "description": "Practical workflow automation for intake, email replies, content drafts, status checks, and reporting, with security and human approval points.",
        },
    ],
    "contact_title": "Need a practical product built from a real workflow?",
    "contact_intro": "Send the business problem, current workflow, and what a useful first version should help users do.",
    "contact_email": "bnvanh@gmail.com",
    "skills": [
        {"name": "Product delivery", "level": 90},
        {"name": "Full-stack web", "level": 75},
        {"name": "Backend APIs", "level": 70},
        {"name": "Automation", "level": 65},
    ],
    "projects": [
        {
            "id": 1,
            "number": "01",
            "name": "Investment Dashboard",
            "audience": "Private investor / portfolio operator",
            "desc": "A personal operating system for a Vietnamese equities portfolio, bringing analysis, journaling, watchlists, and admin CRUD into one deliberate workspace.",
            "outcome": "Demonstrates FastAPI, PostgreSQL persistence, production configuration, and authenticated admin workflows.",
            "tech": ["JavaScript", "FastAPI", "PostgreSQL"],
            "category": "tool",
            "link": "case-studies/investment-dashboard.html",
            "demoLink": "../stocks-app/",
            "github": "https://github.com/robinlebnvanh",
            "date": "Live demo",
            "visual": "dashboard",
            "linkLabel": "Read case study",
            "demoLabel": "Open demo",
        },
        {
            "id": 2,
            "number": "02",
            "name": "Fame Lux Nails & Beauty",
            "audience": "Independent beauty studio",
            "desc": "A refined UK-market nail atelier site, balancing editorial presentation with a booking-oriented enquiry journey.",
            "outcome": "The next productized path is a booking-ready service website package with menu, lead capture, reminders, and dashboard follow-up.",
            "tech": ["HTML", "CSS", "Conversion UX"],
            "category": "frontend",
            "link": "case-studies/fame-lux-nails.html",
            "demoLink": "../nail-landing-page/",
            "github": "https://github.com/robinlebnvanh",
            "date": "Service MVP",
            "visual": "atelier",
            "linkLabel": "Read case study",
            "demoLabel": "Open demo",
        },
        {
            "id": 3,
            "number": "03",
            "name": "Personal AI Agent",
            "audience": "Solo operator / knowledge worker",
            "desc": "A private assistant concept designed around real routines, recurring checks, context-aware task handling, and approval boundaries.",
            "outcome": "Frames automation as a sellable workflow layer: intake, reminders, drafting, reporting, and human-in-the-loop execution.",
            "tech": ["Python", "OpenClaw", "Automation"],
            "category": "tool",
            "link": "case-studies/personal-ai-agent.html",
            "demoLink": "blog.html",
            "github": "https://github.com/robinlebnvanh",
            "date": "Product concept",
            "visual": "agent",
            "linkLabel": "Read case study",
            "demoLabel": "Read notes",
        },
    ],
}


JSON_FIELDS = ("about_body", "offers", "skills", "projects")
EDITABLE_FIELDS = (
    "hero_eyebrow",
    "hero_title",
    "hero_intro",
    "hero_location",
    "hero_experience",
    "about_title",
    "about_body",
    "github_url",
    "studio_title",
    "studio_intro",
    "offers",
    "contact_title",
    "contact_intro",
    "contact_email",
    "skills",
    "projects",
)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _payload_for_storage(values: dict[str, Any]) -> dict[str, Any]:
    payload = dict(values)
    for field in JSON_FIELDS:
        if field in payload:
            payload[field] = _json_dumps(payload[field])
    return payload


def _row_to_content(row: dict[str, Any]) -> dict[str, Any]:
    content = dict(row)
    for field in JSON_FIELDS:
        content[field] = _json_loads(
            content.get(field),
            DEFAULT_PORTFOLIO_CONTENT[field],
        )
    return content


def seed_default_portfolio_content(session: Session) -> None:
    """Insert default portfolio content only when the singleton row is missing."""
    existing = session.scalar(select(func.count()).select_from(portfolio_content))
    if existing:
        return
    session.execute(
        insert(portfolio_content).values(
            id=1,
            **_payload_for_storage(DEFAULT_PORTFOLIO_CONTENT),
        )
    )
    session.commit()


def get_portfolio_content(session: Session) -> dict[str, Any]:
    """Return the singleton portfolio content row."""
    row = session.execute(select(portfolio_content).where(portfolio_content.c.id == 1)).mappings().first()
    if row is None:
        seed_default_portfolio_content(session)
        row = session.execute(select(portfolio_content).where(portfolio_content.c.id == 1)).mappings().one()
    return _row_to_content(dict(row))


def update_portfolio_content(session: Session, values: dict[str, Any]) -> dict[str, Any]:
    """Replace editable portfolio content fields and return the updated row."""
    get_portfolio_content(session)
    payload = _payload_for_storage(
        {field: values[field] for field in EDITABLE_FIELDS if field in values}
    )
    session.execute(
        update(portfolio_content)
        .where(portfolio_content.c.id == 1)
        .values(**payload, updated_at=func.now())
    )
    session.commit()
    return get_portfolio_content(session)
