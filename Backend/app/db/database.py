import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use a local SQLite file instead of looking for a PostgreSQL server
SQLALCHEMY_DATABASE_URL = "sqlite:///./app_data.db"

# Create the SQLAlchemy engine
# SQLite requires 'check_same_thread': False
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
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