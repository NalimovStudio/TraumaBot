from logging.config import fileConfig
from os import environ
from typing import Optional

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url_from_env() -> str:
    """
    Builds the database connection URL from environment variables.
    This ensures alembic uses the same configuration source as the app.
    """
    # Load environment variables from .env file
    load_dotenv()

    def get_env_var(key: str, default: Optional[str] = None) -> str:
        value = environ.get(key)
        if value is None:
            if default is None:
                raise ValueError(f"Environment variable {key} is required but not set")
            return default
        return value

    # Get environment variables
    db_user = get_env_var('DB_USER', 'admin')
    db_password = get_env_var('DB_PASSWORD', '')
    db_host = get_env_var('DB_HOST', 'db')
    db_port = get_env_var('DB_PORT', '5432')
    db_name = get_env_var('DB_NAME', 'psychoAI_db')

    return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


DATABASE_URL = get_url_from_env()

config.set_main_option("sqlalchemy.url", DATABASE_URL + "?async_fallback=True")
print(DATABASE_URL)

from source.infrastructure.database.models.base_model import BaseModel
from source.infrastructure.database.models.user_model import User  # обязательный импорт
from source.infrastructure.database.models.payment_model import PaymentLogs  # обязательный импорт


target_metadata = BaseModel.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
