"""allow repeated budget versions

Revision ID: q0r1s2t3u4v5
Revises: p9q0r1s2t3u4
Create Date: 2026-11-10
"""

from typing import Sequence, Union

from alembic import op


revision: str = "q0r1s2t3u4v5"
down_revision: Union[str, Sequence[str], None] = "p9q0r1s2t3u4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE fin_budget_detail "
        "DROP CONSTRAINT IF EXISTS uq_fin_budget_detail_version"
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_fin_budget_detail_version",
        "fin_budget_detail",
        ["budget_version"],
    )
