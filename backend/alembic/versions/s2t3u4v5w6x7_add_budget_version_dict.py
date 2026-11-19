"""add budget version dictionary

Revision ID: s2t3u4v5w6x7
Revises: r1s2t3u4v5w6
Create Date: 2026-11-11
"""

from datetime import datetime
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "s2t3u4v5w6x7"
down_revision: Union[str, Sequence[str], None] = "r1s2t3u4v5w6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DICT_TYPE = "dim_budget_version"


def upgrade() -> None:
    connection = op.get_bind()
    now = datetime.now()

    dict_type_id = connection.execute(
        sa.text(
            "SELECT id FROM sys_dict_type "
            "WHERE dict_type = :dict_type AND is_deleted = false LIMIT 1"
        ),
        {"dict_type": DICT_TYPE},
    ).scalar_one_or_none()

    if dict_type_id is None:
        dict_type_id = connection.execute(
            sa.text(
                """
                INSERT INTO sys_dict_type (
                    dict_name, dict_type, uuid, status, description,
                    created_time, updated_time, is_deleted, deleted_time
                ) VALUES (
                    :dict_name, :dict_type, :uuid, '0', :description,
                    :created_time, :updated_time, false, NULL
                ) RETURNING id
                """
            ),
            {
                "dict_name": "预算版本",
                "dict_type": DICT_TYPE,
                "uuid": str(uuid4()),
                "description": "预算明细使用的预算版本",
                "created_time": now,
                "updated_time": now,
            },
        ).scalar_one()

    dictionary_items = [
        (1, "年初预算", "primary", "预算版本：年初预算"),
        (2, "管控预算", "warning", "预算版本：管控预算"),
        (3, "A+B预测", "success", "预算版本：A+B预测"),
    ]
    for dict_sort, dict_value, list_class, description in dictionary_items:
        exists = connection.execute(
            sa.text(
                "SELECT id FROM sys_dict_data "
                "WHERE dict_type = :dict_type AND dict_value = :dict_value "
                "AND is_deleted = false LIMIT 1"
            ),
            {"dict_type": DICT_TYPE, "dict_value": dict_value},
        ).scalar_one_or_none()
        if exists:
            continue

        connection.execute(
            sa.text(
                """
                INSERT INTO sys_dict_data (
                    dict_sort, dict_label, dict_value, css_class, list_class,
                    is_default, status, description, dict_type, dict_type_id,
                    uuid, created_time, updated_time, is_deleted, deleted_time
                ) VALUES (
                    :dict_sort, :dict_label, :dict_value, '', :list_class,
                    :is_default, '0', :description, :dict_type, :dict_type_id,
                    :uuid, :created_time, :updated_time, false, NULL
                )
                """
            ),
            {
                "dict_sort": dict_sort,
                "dict_label": dict_value,
                "dict_value": dict_value,
                "list_class": list_class,
                "is_default": dict_sort == 1,
                "description": description,
                "dict_type": DICT_TYPE,
                "dict_type_id": dict_type_id,
                "uuid": str(uuid4()),
                "created_time": now,
                "updated_time": now,
            },
        )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text("DELETE FROM sys_dict_data WHERE dict_type = :dict_type"),
        {"dict_type": DICT_TYPE},
    )
    connection.execute(
        sa.text("DELETE FROM sys_dict_type WHERE dict_type = :dict_type"),
        {"dict_type": DICT_TYPE},
    )
