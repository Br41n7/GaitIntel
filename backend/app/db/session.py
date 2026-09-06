"""
SQLAlchemy engine/session setup.

Kept deliberately boring: one engine, one sessionmaker, one dependency
(`get_db`) that FastAPI routes pull in via Depends(). Swapping Postgres
for anything else SQLAlchemy supports means changing DATABASE_URL only.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
