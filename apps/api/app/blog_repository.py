"""Blog post persistence helpers for the personal site."""

from __future__ import annotations

import json
import sqlite3
from typing import Any


DEFAULT_POSTS = [
    {
        "slug": "backend-blog-api",
        "title": "Building a backend-powered blog",
        "summary": "Why this portfolio stores blog posts in SQLite and serves them through FastAPI.",
        "content": (
            "This log documents the first backend-owned feature in the personal site. "
            "Instead of hardcoding posts in HTML, the browser requests published posts "
            "from FastAPI, and FastAPI reads them from SQLite."
        ),
        "category": "backend",
        "tags": ["FastAPI", "SQLite", "Portfolio"],
        "status": "published",
        "published_at": "2026-08-05",
    },
    {
        "slug": "static-to-fullstack",
        "title": "From static portfolio to full-stack project",
        "summary": "A small feature that shows API design, database ownership, and frontend integration.",
        "content": (
            "The personal site still works as a static GitHub Pages frontend, but the "
            "blog data now belongs to the backend. This is a useful portfolio signal "
            "because it demonstrates a real frontend to backend to database flow."
        ),
        "category": "architecture",
        "tags": ["Frontend", "Backend", "API"],
        "status": "published",
        "published_at": "2026-08-05",
    },
]


def _decode_tags(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        tags = json.loads(value)
    except json.JSONDecodeError:
        return []
    return tags if isinstance(tags, list) else []


def _row_to_post(row: sqlite3.Row, include_content: bool = False) -> dict[str, Any]:
    post = {
        "id": row["id"],
        "slug": row["slug"],
        "title": row["title"],
        "summary": row["summary"],
        "category": row["category"],
        "tags": _decode_tags(row["tags"]),
        "published_at": row["published_at"],
        "updated_at": row["updated_at"],
    }
    if include_content:
        post["content"] = row["content"]
    return post


def seed_default_blog_posts(connection: sqlite3.Connection) -> None:
    """Insert starter posts only when the blog table is empty."""
    existing = connection.execute("SELECT COUNT(*) FROM blog_posts").fetchone()[0]
    if existing:
        return

    connection.executemany(
        """
        INSERT INTO blog_posts
            (slug, title, summary, content, category, tags, status, published_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            (
                post["slug"],
                post["title"],
                post["summary"],
                post["content"],
                post["category"],
                json.dumps(post["tags"]),
                post["status"],
                post["published_at"],
            )
            for post in DEFAULT_POSTS
        ),
    )
    connection.commit()


def list_published_posts(
    connection: sqlite3.Connection,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    """Return paginated published blog posts."""
    total = connection.execute(
        "SELECT COUNT(*) FROM blog_posts WHERE status = 'published'"
    ).fetchone()[0]
    rows = connection.execute(
        """
        SELECT id, slug, title, summary, category, tags, published_at, updated_at
        FROM blog_posts
        WHERE status = 'published'
        ORDER BY published_at DESC, id DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ).fetchall()

    return {
        "posts": [_row_to_post(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(rows) < total,
    }


def get_published_post(
    connection: sqlite3.Connection,
    slug: str,
) -> dict[str, Any] | None:
    """Return one published blog post by slug."""
    row = connection.execute(
        """
        SELECT id, slug, title, summary, content, category, tags, published_at, updated_at
        FROM blog_posts
        WHERE slug = ? AND status = 'published'
        """,
        (slug,),
    ).fetchone()
    return _row_to_post(row, include_content=True) if row else None
