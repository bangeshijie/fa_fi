from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.api.v1.module_system.dept.model import DeptModel
from app.api.v1.module_system.dict.model import DictDataModel, DictTypeModel
from app.api.v1.module_system.log.model import OperationLogModel
from app.api.v1.module_system.menu.model import MenuModel
from app.api.v1.module_system.notice.model import NoticeModel
from app.api.v1.module_system.params.model import ParamsModel
from app.api.v1.module_system.position.model import PositionModel
from app.api.v1.module_system.role.model import (
    RoleDeptsModel,
    RoleMenusModel,
    RoleModel,
)
from app.api.v1.module_system.user.model import (
    UserModel,
    UserPositionsModel,
    UserRolesModel,
)
from app.config.setting import settings
from app.core.base_model import MappedBase


# 保留这些模型的导入，使所有表都注册到 MappedBase.metadata，支持 autogenerate。
_MODEL_CLASSES = (
    DeptModel,
    DictDataModel,
    DictTypeModel,
    MenuModel,
    NoticeModel,
    OperationLogModel,
    ParamsModel,
    PositionModel,
    RoleDeptsModel,
    RoleMenusModel,
    RoleModel,
    UserModel,
    UserPositionsModel,
    UserRolesModel,
)


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = MappedBase.metadata


def get_database_url() -> str:
    """使用项目统一的 SQLAlchemy 数据库连接地址。"""
    return settings.DB_URI


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connect_args = (
        {"options": f"-c timezone={settings.TIMEZONE}"}
        if settings.DATABASE_TYPE == "postgres"
        else {}
    )

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
