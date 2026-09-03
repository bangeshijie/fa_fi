"""normalize existing timestamp data to Beijing time

Revision ID: a1b2c3d4e5f6
Revises: f9f0de2bdaec
Create Date: 2026-09-01

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f9f0de2bdaec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ModelMixin 使用 timestamp without time zone 保存审计时间。
# 旧服务在 UTC 容器中写入了 UTC 的时钟值，因此需要统一加 8 小时。
_AUDIT_TABLES = (
    "sys_dept",
    "sys_dict_type",
    "sys_dict_data",
    "sys_menu",
    "sys_param",
    "sys_role",
    "sys_user",
    "sys_log",
    "sys_notice",
    "sys_position",
)


def upgrade() -> None:
    """将历史无时区 UTC 审计时间修正为北京时间。"""
    op.execute(sa.text("SET TIME ZONE 'Asia/Shanghai'"))

    for table_name in _AUDIT_TABLES:
        op.execute(
            sa.text(
                f"""
                UPDATE {table_name}
                SET created_time = created_time + INTERVAL '8 hours',
                    updated_time = updated_time + INTERVAL '8 hours',
                    deleted_time = CASE
                        WHEN deleted_time IS NULL THEN NULL
                        ELSE deleted_time + INTERVAL '8 hours'
                    END
                """
            )
        )


def downgrade() -> None:
    """回退历史审计时间修正。"""
    op.execute(sa.text("SET TIME ZONE 'Asia/Shanghai'"))

    for table_name in reversed(_AUDIT_TABLES):
        op.execute(
            sa.text(
                f"""
                UPDATE {table_name}
                SET created_time = created_time - INTERVAL '8 hours',
                    updated_time = updated_time - INTERVAL '8 hours',
                    deleted_time = CASE
                        WHEN deleted_time IS NULL THEN NULL
                        ELSE deleted_time - INTERVAL '8 hours'
                    END
                """
            )
        )
