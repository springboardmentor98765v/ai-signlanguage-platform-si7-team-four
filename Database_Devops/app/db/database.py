import os
import uuid as _uuid_module
from sqlalchemy import create_engine, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.types import TypeDecorator
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://signlang:signlang_dev_pw@localhost:5432/signlang_db")
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, pool_recycle=280)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class PortableUUID(TypeDecorator):
    """
    UUID column type that works identically on SQLite and PostgreSQL.
    """
    impl = String(36)
    cache_ok = True

    def __init__(self, as_uuid=None, **kwargs):
        super().__init__()
        self.as_uuid = as_uuid

    def load_dialect_impl(self, dialect):
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
