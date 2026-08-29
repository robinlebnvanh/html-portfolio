"""Add cover image metadata to blog posts.

Revision ID: 0009_blog_post_images
Revises: 0008_admin_audit_logs
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0009_blog_post_images"
down_revision: Union[str, Sequence[str], None] = "0008_admin_audit_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("blog_posts", sa.Column("cover_image_url", sa.Text()))
    op.add_column("blog_posts", sa.Column("cover_image_alt", sa.String(length=220)))


def downgrade() -> None:
    op.drop_column("blog_posts", "cover_image_alt")
    op.drop_column("blog_posts", "cover_image_url")
