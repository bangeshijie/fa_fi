"""rename budget version values and accounting subject category

Revision ID: u4v5w6x7y8z9
Revises: s2t3u4v5w6x7
Create Date: 2026-11-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "u4v5w6x7y8z9"
down_revision: Union[str, Sequence[str], None] = "s2t3u4v5w6x7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            UPDATE fin_budget_detail
            SET budget_version = CASE budget_version
                WHEN '年初预算' THEN 'YBB'
                WHEN '管控预算' THEN 'MCB'
                WHEN 'A+B预测' THEN 'ABF'
                ELSE budget_version
            END
            WHERE budget_version IN ('年初预算', '管控预算', 'A+B预测')
            """
        )
    )

    dictionary_values = [
        ("年初预算", "YBB", "预算版本：YBB 年初预算"),
        ("管控预算", "MCB", "预算版本：MCB 管控预算"),
        ("A+B预测", "ABF", "预算版本：ABF A+B预测"),
    ]
    for old_value, new_value, description in dictionary_values:
        connection.execute(
            sa.text(
                """
                UPDATE sys_dict_data
                SET dict_value = :new_value,
                    description = :description,
                    updated_time = CURRENT_TIMESTAMP
                WHERE dict_type = 'dim_budget_version'
                  AND dict_value = :old_value
                """
            ),
            {
                "old_value": old_value,
                "new_value": new_value,
                "description": description,
            },
        )

    op.alter_column(
        "dim_accounting_subject",
        "management_statement_subject",
        new_column_name="management_category_level3",
        existing_type=sa.String(length=128),
        existing_nullable=True,
        comment="管理科目三级分类",
    )


def downgrade() -> None:
    connection = op.get_bind()

    op.alter_column(
        "dim_accounting_subject",
        "management_category_level3",
        new_column_name="management_statement_subject",
        existing_type=sa.String(length=128),
        existing_nullable=True,
        comment="所属管理报表科目",
    )

    connection.execute(
        sa.text(
            """
            UPDATE fin_budget_detail
            SET budget_version = CASE budget_version
                WHEN 'YBB' THEN '年初预算'
                WHEN 'MCB' THEN '管控预算'
                WHEN 'ABF' THEN 'A+B预测'
                ELSE budget_version
            END
            WHERE budget_version IN ('YBB', 'MCB', 'ABF')
            """
        )
    )

    dictionary_values = [
        ("YBB", "年初预算", "预算版本：年初预算"),
        ("MCB", "管控预算", "预算版本：管控预算"),
        ("ABF", "A+B预测", "预算版本：A+B预测"),
    ]
    for old_value, new_value, description in dictionary_values:
        connection.execute(
            sa.text(
                """
                UPDATE sys_dict_data
                SET dict_value = :new_value,
                    description = :description,
                    updated_time = CURRENT_TIMESTAMP
                WHERE dict_type = 'dim_budget_version'
                  AND dict_value = :old_value
                """
            ),
            {
                "old_value": old_value,
                "new_value": new_value,
                "description": description,
            },
        )
