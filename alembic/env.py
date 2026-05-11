from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Connection

from alembic import context

from app.core.config import settings
from app.db.session import Base

import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _sync_url(url: str) -> str:
    """
    Convert an asyncpg URL to a psycopg2-compatible synchronous URL.

    Handles two issues:
    1. asyncpg prepared statements conflict with PgBouncer transaction-mode
       pooling — psycopg2 avoids this entirely.
    2. asyncpg accepts ?ssl=require but psycopg2 requires ?sslmode=require.
    """
    from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

    # Normalise scheme: strip +asyncpg driver suffix, ensure postgresql://
    for prefix in ("postgresql+asyncpg://", "postgres+asyncpg://"):
        if url.startswith(prefix):
            url = "postgresql://" + url[len(prefix):]
            break
    else:
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]

    # Translate asyncpg SSL params → psycopg2 SSL params
    # asyncpg: ?ssl=require / ?ssl=true / ?ssl=1
    # psycopg2: ?sslmode=require
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    ssl_val = params.pop("ssl", None)
    if ssl_val and ssl_val[0].lower() in ("require", "true", "1", "verify-ca", "verify-full"):
        params.setdefault("sslmode", ["require"])

    new_query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=new_query))


def run_migrations_offline() -> None:
    context.configure(
        url=_sync_url(settings.DATABASE_URL),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        _sync_url(settings.DATABASE_URL),
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        do_run_migrations(connection)
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
