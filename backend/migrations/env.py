from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, make_url, pool

from app.config import settings
from app.database import models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = make_url(settings.database_url)
if database_url.drivername == "sqlite+aiosqlite":
    database_url = database_url.set(drivername="sqlite")
elif database_url.drivername in {"postgresql", "postgresql+asyncpg"}:
    database_url = database_url.set(drivername="postgresql+psycopg")
sync_database_url = database_url.render_as_string(hide_password=False)
config.set_main_option("sqlalchemy.url", sync_database_url.replace("%", "%%"))
target_metadata = models.Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=sync_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
