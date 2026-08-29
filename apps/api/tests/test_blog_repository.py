"""Behavior tests for the SQLAlchemy blog repository."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import insert

from app.blog_repository import (
    blog_slug_exists,
    count_admin_posts,
    create_blog_post,
    delete_blog_post,
    get_published_post,
    list_admin_posts,
    list_published_posts,
    seed_default_blog_posts,
    update_blog_post,
)
from app.database import initialize_database
from app.sqlalchemy_database import get_engine, get_session, get_session_factory
from app.sqlalchemy_tables import blog_posts


class BlogRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "blog.sqlite3"
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

    def test_seed_and_list_published_posts_preserve_api_shape(self) -> None:
        seed_default_blog_posts(self.session)

        result = list_published_posts(self.session, limit=1, offset=0)

        self.assertEqual(result["total"], 2)
        self.assertEqual(result["limit"], 1)
        self.assertEqual(result["offset"], 0)
        self.assertTrue(result["has_more"])
        self.assertEqual(len(result["posts"]), 1)
        self.assertIn("tags", result["posts"][0])
        self.assertNotIn("content", result["posts"][0])

    def test_get_published_post_returns_content_and_hides_drafts(self) -> None:
        self.session.execute(
            insert(blog_posts),
            [
                {
                    "slug": "published-post",
                    "title": "Published post",
                    "summary": "Visible",
                    "content": "Full content",
                    "category": "backend",
                    "tags": '["FastAPI"]',
                    "status": "published",
                    "published_at": "2026-08-06",
                },
                {
                    "slug": "draft-post",
                    "title": "Draft post",
                    "summary": "Hidden",
                    "content": "Draft content",
                    "category": "backend",
                    "tags": "[]",
                    "status": "draft",
                    "published_at": None,
                },
            ],
        )
        self.session.commit()

        post = get_published_post(self.session, "published-post")

        self.assertIsNotNone(post)
        self.assertEqual(post["content"], "Full content")
        self.assertEqual(post["tags"], ["FastAPI"])
        self.assertIsNone(get_published_post(self.session, "draft-post"))

    def test_admin_crud_manages_database_posts(self) -> None:
        created = create_blog_post(
            self.session,
            {
                "slug": "admin-draft",
                "title": "Admin draft",
                "summary": "Managed through the admin API",
                "content": "Draft content",
                "category": "backend",
                "tags": ["FastAPI", "CRUD"],
                "status": "draft",
                "published_at": None,
            },
        )

        self.assertEqual(created["status"], "draft")
        self.assertEqual(created["tags"], ["FastAPI", "CRUD"])
        self.assertTrue(blog_slug_exists(self.session, "admin-draft"))
        self.assertEqual(list_admin_posts(self.session)["total"], 1)
        self.assertEqual(count_admin_posts(self.session), 1)
        self.assertEqual(list_published_posts(self.session, limit=4, offset=0)["total"], 0)

        updated = update_blog_post(
            self.session,
            created["id"],
            {
                "slug": "admin-published",
                "title": "Admin published",
                "summary": "Visible after publishing",
                "content": "Published content",
                "category": "portfolio",
                "tags": ["PostgreSQL"],
                "status": "published",
                "published_at": "2026-08-27",
            },
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["slug"], "admin-published")
        self.assertEqual(updated["status"], "published")
        self.assertEqual(updated["tags"], ["PostgreSQL"])
        self.assertEqual(list_published_posts(self.session, limit=4, offset=0)["total"], 1)

        self.assertTrue(delete_blog_post(self.session, created["id"]))
        self.assertFalse(delete_blog_post(self.session, created["id"]))
        self.assertEqual(list_admin_posts(self.session)["total"], 0)
        self.assertEqual(count_admin_posts(self.session), 0)


if __name__ == "__main__":
    unittest.main()
