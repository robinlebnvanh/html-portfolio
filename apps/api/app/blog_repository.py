"""Blog post persistence helpers for the personal site."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.orm import Session

from app.sqlalchemy_tables import blog_posts


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


def _row_to_post(row: dict[str, Any], include_content: bool = False) -> dict[str, Any]:
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


def _row_to_admin_post(row: dict[str, Any]) -> dict[str, Any]:
    post = _row_to_post(row, include_content=True)
    post["status"] = row["status"]
    return post


def _encode_tags(tags: list[str] | None) -> str:
    cleaned = [tag.strip() for tag in tags or [] if tag.strip()]
    return json.dumps(cleaned)


def seed_default_blog_posts(session: Session) -> None:
    """Insert starter posts only when the blog table is empty."""
    existing = session.scalar(select(func.count()).select_from(blog_posts))
    if existing:
        return

    session.execute(
        insert(blog_posts),
        [
            {
                "slug": post["slug"],
                "title": post["title"],
                "summary": post["summary"],
                "content": post["content"],
                "category": post["category"],
                "tags": json.dumps(post["tags"]),
                "status": post["status"],
                "published_at": post["published_at"],
            }
            for post in DEFAULT_POSTS
        ],
    )
    session.commit()


def list_published_posts(session: Session, limit: int, offset: int) -> dict[str, Any]:
    """Return paginated published blog posts."""
    total = session.scalar(
        select(func.count()).where(blog_posts.c.status == "published")
    )
    rows = session.execute(
        select(
            blog_posts.c.id,
            blog_posts.c.slug,
            blog_posts.c.title,
            blog_posts.c.summary,
            blog_posts.c.category,
            blog_posts.c.tags,
            blog_posts.c.published_at,
            blog_posts.c.updated_at,
        )
        .where(blog_posts.c.status == "published")
        .order_by(blog_posts.c.published_at.desc(), blog_posts.c.id.desc())
        .limit(limit)
        .offset(offset)
    ).mappings().all()

    return {
        "posts": [_row_to_post(dict(row)) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(rows) < total,
    }


def get_published_post(session: Session, slug: str) -> dict[str, Any] | None:
    """Return one published blog post by slug."""
    row = session.execute(
        select(
            blog_posts.c.id,
            blog_posts.c.slug,
            blog_posts.c.title,
            blog_posts.c.summary,
            blog_posts.c.content,
            blog_posts.c.category,
            blog_posts.c.tags,
            blog_posts.c.published_at,
            blog_posts.c.updated_at,
        )
        .where(blog_posts.c.slug == slug, blog_posts.c.status == "published")
    ).mappings().first()
    return _row_to_post(dict(row), include_content=True) if row else None


def list_admin_posts(
    session: Session,
    status_filter: str | None = None,
) -> dict[str, Any]:
    """Return all blog posts for the admin UI."""
    filters = []
    if status_filter:
        filters.append(blog_posts.c.status == status_filter)

    total_query = select(func.count()).select_from(blog_posts)
    if filters:
        total_query = total_query.where(*filters)
    total = session.scalar(total_query)
    rows = session.execute(
        select(
            blog_posts.c.id,
            blog_posts.c.slug,
            blog_posts.c.title,
            blog_posts.c.summary,
            blog_posts.c.content,
            blog_posts.c.category,
            blog_posts.c.tags,
            blog_posts.c.status,
            blog_posts.c.published_at,
            blog_posts.c.updated_at,
        )
        .where(*filters)
        .order_by(blog_posts.c.updated_at.desc(), blog_posts.c.id.desc())
    ).mappings().all()

    return {
        "posts": [_row_to_admin_post(dict(row)) for row in rows],
        "total": total,
    }


def count_admin_posts(session: Session) -> int:
    """Return the total number of database-backed blog posts."""

    return int(session.scalar(select(func.count()).select_from(blog_posts)) or 0)


def blog_slug_exists(session: Session, slug: str, exclude_post_id: int | None = None) -> bool:
    """Return whether another blog post already uses the slug."""
    query = select(func.count()).where(blog_posts.c.slug == slug)
    if exclude_post_id is not None:
        query = query.where(blog_posts.c.id != exclude_post_id)
    return bool(session.scalar(query))


def create_blog_post(session: Session, values: dict[str, Any]) -> dict[str, Any]:
    """Create a blog post and return the admin shape."""
    payload = {
        "slug": values["slug"],
        "title": values["title"],
        "summary": values["summary"],
        "content": values["content"],
        "category": values["category"],
        "tags": _encode_tags(values.get("tags")),
        "status": values["status"],
        "published_at": values.get("published_at"),
    }
    if payload["status"] == "published" and not payload["published_at"]:
        payload["published_at"] = date.today().isoformat()

    result = session.execute(insert(blog_posts).values(payload))
    session.commit()
    post_id = result.inserted_primary_key[0]
    created = get_admin_post(session, post_id)
    if created is None:
        raise RuntimeError("created blog post could not be loaded")
    return created


def get_admin_post(session: Session, post_id: int) -> dict[str, Any] | None:
    """Return one blog post by id for admin flows."""
    row = session.execute(
        select(
            blog_posts.c.id,
            blog_posts.c.slug,
            blog_posts.c.title,
            blog_posts.c.summary,
            blog_posts.c.content,
            blog_posts.c.category,
            blog_posts.c.tags,
            blog_posts.c.status,
            blog_posts.c.published_at,
            blog_posts.c.updated_at,
        ).where(blog_posts.c.id == post_id)
    ).mappings().first()
    return _row_to_admin_post(dict(row)) if row else None


def update_blog_post(
    session: Session,
    post_id: int,
    changes: dict[str, Any],
) -> dict[str, Any] | None:
    """Update a blog post and return the admin shape."""
    if not changes:
        return get_admin_post(session, post_id)

    payload = dict(changes)
    if "tags" in payload:
        payload["tags"] = _encode_tags(payload["tags"])
    if payload.get("status") == "published" and not payload.get("published_at"):
        existing = get_admin_post(session, post_id)
        if existing is not None and not existing["published_at"]:
            payload["published_at"] = date.today().isoformat()
    payload["updated_at"] = func.current_timestamp()

    result = session.execute(
        update(blog_posts).where(blog_posts.c.id == post_id).values(payload)
    )
    if result.rowcount == 0:
        session.rollback()
        return None

    session.commit()
    return get_admin_post(session, post_id)


def delete_blog_post(session: Session, post_id: int) -> bool:
    """Delete one blog post."""
    result = session.execute(delete(blog_posts).where(blog_posts.c.id == post_id))
    if result.rowcount == 0:
        session.rollback()
        return False
    session.commit()
    return True
