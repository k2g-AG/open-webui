"""Add stripe_customer_id to user table

Revision ID: d9e4f8b2c1a3
Revises: 018012973d35
Create Date: 2025-01-14 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d9e4f8b2c1a3"
down_revision: Union[str, None] = "018012973d35"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add stripe_customer_id column to user table
    op.add_column("user", sa.Column("stripe_customer_id", sa.String(), nullable=True))


def downgrade() -> None:
    # Remove stripe_customer_id column from user table
    op.drop_column("user", "stripe_customer_id")
