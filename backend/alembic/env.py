
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context
from app.core.config import settings
from app.core.database import Base
from app.models.profile import Profile  # noqa: F401
from app.models.simulation_session import SimulationSessionModel
from app.models.simulation_event import SimulationEventModel
from app.models.simulation_action_request import SimulationActionRequestModel

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def get_migration_url() -> str:
    """
    Alembic must use a dedicated migration connection.

    Never silently fall back to the application's
    runtime database credentials.
    """
    if not settings.migration_database_url:
        raise RuntimeError(
            "MIGRATION_DATABASE_URL is not configured."
        )

    return settings.migration_database_url


def include_name(name, type_, parent_names):
    """
    Prevent Alembic autogenerate from suggesting
    deletion of unrelated Supabase tables.
    """
    if type_ == "table":
        return name in target_metadata.tables

    return True


def run_migrations_offline():
    context.configure(
        url=get_migration_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_name=include_name,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(
        get_migration_url(),
        poolclass=pool.NullPool,
        connect_args={"sslmode": "require"},
    )

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_name=include_name,
                compare_type=True,
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
