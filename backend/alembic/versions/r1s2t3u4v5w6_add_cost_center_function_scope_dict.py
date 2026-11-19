"""add cost center function scope dictionary

Revision ID: r1s2t3u4v5w6
Revises: q0r1s2t3u4v5
Create Date: 2026-11-11
"""

from datetime import datetime
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "r1s2t3u4v5w6"
down_revision: Union[str, Sequence[str], None] = "q0r1s2t3u4v5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DICT_TYPE = "dim_cost_center_function_scope"


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
                "dict_name": "成本中心职能范围",
                "dict_type": DICT_TYPE,
                "uuid": str(uuid4()),
                "description": "成本中心职能范围代码与名称映射",
                "created_time": now,
                "updated_time": now,
            },
        ).scalar_one()

    dictionary_items = [
        (1, "销售", "4000", "primary", "成本中心职能范围：销售"),
        (2, "管理", "5000", "warning", "成本中心职能范围：管理"),
        (3, "研发", "5500", "success", "成本中心职能范围：研发"),
    ]
    for dict_sort, dict_label, dict_value, list_class, description in dictionary_items:
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
                    false, '0', :description, :dict_type, :dict_type_id,
                    :uuid, :created_time, :updated_time, false, NULL
                )
                """
            ),
            {
                "dict_sort": dict_sort,
                "dict_label": dict_label,
                "dict_value": dict_value,
                "list_class": list_class,
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
