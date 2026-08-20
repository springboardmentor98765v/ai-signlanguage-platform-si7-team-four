import os
import uuid as _uuid_module
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TypeDecorator

# Prefer the repo-root .env (shared Neon DATABASE_URL) over any nested
# Backend/app/.env so every launch uses the same production database, and
# never override a DATABASE_URL injected by docker-compose or the shell.
_REPO_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
if _REPO_ROOT_ENV.exists():
    load_dotenv(dotenv_path=_REPO_ROOT_ENV, override=False)
load_dotenv(override=False)


class PortableUUID(TypeDecorator):
    """
    UUID column type that works identically on SQLite and PostgreSQL.

    The built-in postgresql.UUID type compiles to CHAR(32) on SQLite, whose
    NUMERIC column affinity silently coerces all-numeric 32-char strings into
    INTEGER/FLOAT values, corrupting ids on read. This type instead stores a
    canonical 36-char dashed UUID string (String(36)) on every dialect so UUID
    columns always behave the same in dev, tests, and production. Values are
    canonicalized on bind; legacy/flat values are re-canonicalized on read.
    """
    impl = String(36)
    cache_ok = True

    def __init__(self, as_uuid=None, **kwargs):
        super().__init__()
        self.as_uuid = as_uuid

    def load_dialect_impl(self, dialect):
        # PostgreSQL expects its native UUID type so foreign keys referencing
        # users.id (native uuid on the production Neon DB) remain compatible.
        # SQLite keeps the portable VARCHAR(36) representation.
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID())
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        try:
            return str(_uuid_module.UUID(str(value)))
        except (ValueError, AttributeError, TypeError):
            return str(_uuid_module.uuid5(_uuid_module.NAMESPACE_DNS, str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return str(_uuid_module.UUID(str(value)))
        except (ValueError, AttributeError, TypeError):
            return str(value)


load_dotenv()

# The database URL is configurable via DATABASE_URL (e.g. a deployed Neon
# PostgreSQL URL) and falls back to a local SQLite file for development.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app_data.db")

# If the configured URL uses a DB driver that is not installed in this
# environment (e.g. running the repo locally without the postgres package),
# gracefully fall back to the local SQLite engine instead of crashing at
# import time. Deployed containers install the driver, so they keep using
# the real DATABASE_URL. Production config is still validated upstream by
# predeploy/config_check.py.
def _driver_available(url: str) -> bool:
    scheme = url.split(":", 1)[0].split("+", 1)[0].lower()
    driver_by_scheme = {
        "postgresql": ("psycopg2", "psycopg", "pg8000"),
        "mysql": ("pymysql", "mysqlclient"),
        "mariadb": ("pymysql", "mysqlclient"),
    }
    candidates = driver_by_scheme.get(scheme, ())
    if not candidates:
        return True
    for candidate in candidates:
        try:
            __import__(candidate)
            return True
        except ImportError:
            continue
    return False


if DATABASE_URL.startswith("sqlite") or not _driver_available(DATABASE_URL):
    if not DATABASE_URL.startswith("sqlite"):
        print(f"WARNING: DATABASE_URL driver unavailable; falling back to local SQLite.")
        DATABASE_URL = "sqlite:///./app_data.db"
    # SQLite requires 'check_same_thread': False
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for the models to inherit from
Base = declarative_base()

# Dependency to get the database session in routers
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()