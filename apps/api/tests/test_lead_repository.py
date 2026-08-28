"""Behavior tests for service-business lead persistence."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app.database import initialize_database
from app.lead_repository import (
    create_lead,
    create_lead_activity,
    list_lead_activities,
    list_leads,
    update_lead,
)
from app.sqlalchemy_database import get_engine, get_session, get_session_factory


class LeadRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "leads.sqlite3"
        os.environ["PRJ008_DB_PATH"] = str(database_path)
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        initialize_database()
        self.session = get_session()

    def tearDown(self) -> None:
        self.session.close()
        get_session_factory.cache_clear()
        get_engine.cache_clear()
        os.environ.pop("PRJ008_DB_PATH", None)
        self.temp_dir.cleanup()

    def test_create_and_list_leads_newest_first(self) -> None:
        first = create_lead(
            self.session,
            {
                "source": "photography-studio-demo",
                "business_name": "Vow & Bloom Studio",
                "customer_name": "Ava Nguyen",
                "email": "ava@example.com",
                "preferred_date": "2026-09-20",
                "package_name": "Wedding Story",
                "message": "Outdoor wedding with 80 guests.",
            },
        )
        second = create_lead(
            self.session,
            {
                "source": "wedding-planner-demo",
                "business_name": "Maison Vow",
                "customer_name": "Minh Tran",
                "email": "minh@example.com",
                "preferred_date": "2026-10-12",
                "package_name": "Partial Planning",
                "message": "Need vendor coordination.",
            },
        )

        result = list_leads(self.session)

        self.assertEqual(result["total"], 2)
        self.assertEqual(result["leads"][0]["id"], second["id"])
        self.assertEqual(result["leads"][1]["id"], first["id"])
        self.assertEqual(first["status"], "new")
        self.assertEqual(first["channel"], "form")

    def test_update_lead_status_and_filter(self) -> None:
        lead = create_lead(
            self.session,
            {
                "source": "service-business-kit",
                "business_name": "Everline Studio",
                "customer_name": "Client One",
                "email": "client@example.com",
                "preferred_date": "2026-09-01",
                "package_name": "Booking-Ready Site",
                "message": "Need a service website.",
            },
        )

        updated = update_lead(
            self.session,
            lead["id"],
            {"status": "proposal_sent", "admin_note": "Send package outline."},
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["status"], "proposal_sent")
        self.assertEqual(updated["admin_note"], "Send package outline.")
        self.assertEqual(list_leads(self.session, "new")["total"], 0)
        self.assertEqual(list_leads(self.session, "proposal_sent")["total"], 1)

    def test_create_manual_phone_lead_and_activity(self) -> None:
        lead = create_lead(
            self.session,
            {
                "source": "admin-manual",
                "channel": "phone",
                "business_name": "Robin Le Portfolio",
                "customer_name": "Phone Client",
                "phone": "0900000000",
                "follow_up_at": "2026-09-02",
                "package_name": "Portfolio contact",
                "message": "Called to ask about a booking workflow.",
            },
        )

        activity = create_lead_activity(
            self.session,
            lead["id"],
            {"activity_type": "phone_call", "note": "Asked for a follow-up email."},
        )
        activities = list_lead_activities(self.session, lead["id"])

        self.assertEqual(lead["channel"], "phone")
        self.assertIsNone(lead["email"])
        self.assertEqual(lead["phone"], "0900000000")
        self.assertEqual(lead["follow_up_at"], "2026-09-02")
        self.assertIsNotNone(activity)
        self.assertEqual(activities["total"], 1)
        self.assertEqual(activities["activities"][0]["note"], "Asked for a follow-up email.")

    def test_update_missing_lead_returns_none(self) -> None:
        self.assertIsNone(update_lead(self.session, 999, {"status": "closed"}))


if __name__ == "__main__":
    unittest.main()
