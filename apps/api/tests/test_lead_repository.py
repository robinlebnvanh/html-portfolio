"""Behavior tests for service-business lead persistence."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app.database import initialize_database
from app.lead_repository import (
    count_leads,
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
        self.assertEqual(count_leads(self.session), 2)

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

    def test_search_leads_by_customer_package_or_message(self) -> None:
        create_lead(
            self.session,
            {
                "source": "photoshop-retouching-vi",
                "business_name": "Robin Photoshop",
                "customer_name": "Mai Nguyen",
                "email": "mai@example.com",
                "phone": "0900000000",
                "package_name": "Retouch Chan Dung",
                "message": "Can chinh anh CV.",
            },
        )
        create_lead(
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

        result = list_leads(self.session, search="retouch")

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["leads"][0]["customer_name"], "Mai Nguyen")

    def test_update_photoshop_job_tracking_fields(self) -> None:
        lead = create_lead(
            self.session,
            {
                "source": "photoshop-retouching-au",
                "business_name": "Robin Photoshop",
                "customer_name": "Ava Client",
                "email": "ava@example.com",
                "package_name": "Product photo cleanup",
                "message": "Need 12 product photos retouched.",
            },
        )

        updated = update_lead(
            self.session,
            lead["id"],
            {
                "status": "booked",
                "job_stage": "editing",
                "quoted_amount": 180,
                "quote_currency": "AUD",
                "deadline_at": "2026-09-04",
                "file_url": "https://drive.example/files",
                "delivery_url": "https://drive.example/delivery",
                "revision_count": 1,
                "paid_at": "2026-09-05",
            },
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["status"], "booked")
        self.assertEqual(updated["job_stage"], "editing")
        self.assertEqual(updated["quoted_amount"], 180)
        self.assertEqual(updated["quote_currency"], "AUD")
        self.assertEqual(updated["deadline_at"], "2026-09-04")
        self.assertEqual(updated["file_url"], "https://drive.example/files")
        self.assertEqual(updated["delivery_url"], "https://drive.example/delivery")
        self.assertEqual(updated["revision_count"], 1)
        self.assertEqual(updated["paid_at"], "2026-09-05")

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
