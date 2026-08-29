"""Add quantity to stock trades.

Revision ID: 0007_trade_quantity
Revises: 0006_lead_job_tracking
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_trade_quantity"
down_revision: Union[str, Sequence[str], None] = "0006_lead_job_tracking"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("trades") as batch_op:
        batch_op.add_column(
            sa.Column("quantity", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.create_check_constraint(
            "ck_trades_quantity_nonnegative",
            "quantity >= 0",
        )


def downgrade() -> None:
    with op.batch_alter_table("trades") as batch_op:
        batch_op.drop_constraint("ck_trades_quantity_nonnegative", type_="check")
        batch_op.drop_column("quantity")
