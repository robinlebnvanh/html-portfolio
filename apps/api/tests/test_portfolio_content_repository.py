"""Behavior tests for managed portfolio content."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app.database import initialize_database
from app.portfolio_content_repository import (
    get_portfolio_content,
    seed_default_portfolio_content,
    sync_default_portfolio_projects,
    update_portfolio_content,
)
from app.sqlalchemy_database import get_engine, get_session, get_session_factory


class PortfolioContentRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "portfolio-content.sqlite3"
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

    def test_seed_default_content_preserves_public_shape(self) -> None:
        seed_default_portfolio_content(self.session)

        content = get_portfolio_content(self.session)

        self.assertEqual(content["hero_title"], "Building full-stack tools people can actually use.")
        self.assertGreaterEqual(len(content["skills"]), 1)
        self.assertGreaterEqual(len(content["projects"]), 1)
        self.assertIn("offers", content)

    def test_update_portfolio_content_replaces_editable_fields(self) -> None:
        original = get_portfolio_content(self.session)
        updated_payload = {
            **original,
            "hero_title": "Managed from Admin Console",
            "about_body": ["Updated paragraph"],
            "skills": [{"name": "Backend APIs", "level": 88}],
            "offers": [
                {
                    "kicker": "Offer 01",
                    "title": "Admin-managed offer",
                    "description": "Updated through the authenticated CMS flow.",
                }
            ],
            "projects": [
                {
                    "id": 1,
                    "number": "01",
                    "name": "Admin-managed project",
                    "audience": "Portfolio reviewer",
                    "desc": "Updated project description",
                    "outcome": "Shows managed portfolio content.",
                    "tech": ["FastAPI"],
                    "category": "tool",
                    "link": "case-studies/investment-dashboard.html",
                    "demoLink": "../stocks-app/",
                    "github": "https://github.com/robinlebnvanh",
                    "date": "Managed",
                    "visual": "dashboard",
                    "linkLabel": "Read case study",
                    "demoLabel": "Open demo",
                }
            ],
        }

        updated = update_portfolio_content(self.session, updated_payload)

        self.assertEqual(updated["hero_title"], "Managed from Admin Console")
        self.assertEqual(updated["about_body"], ["Updated paragraph"])
        self.assertEqual(updated["skills"], [{"name": "Backend APIs", "level": 88}])
        self.assertEqual(updated["offers"][0]["title"], "Admin-managed offer")
        self.assertEqual(updated["projects"][0]["name"], "Admin-managed project")

    def test_sync_default_portfolio_projects_appends_missing_projects(self) -> None:
        original = get_portfolio_content(self.session)
        update_portfolio_content(
            self.session,
            {
                **original,
                "hero_title": "Keep managed headline",
                "projects": original["projects"][:3],
            },
        )

        sync_default_portfolio_projects(self.session)

        updated = get_portfolio_content(self.session)
        self.assertEqual(updated["hero_title"], "Keep managed headline")
        self.assertEqual(len(updated["projects"]), len(original["projects"]))
        self.assertEqual(
            [project["name"] for project in updated["projects"][3:]],
            [
                "Service Business Website Kit",
                "Photography Studio Demo",
                "Wedding Planner Demo",
                "Photoshop Retouching Service",
            ],
        )


if __name__ == "__main__":
    unittest.main()
