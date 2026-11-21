"""MySQL connection and SQLAlchemy session helpers."""

import os
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from dotenv import load_dotenv


load_dotenv()


class Base(DeclarativeBase):
    """Base class for database models."""


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured.")

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


@lru_cache(maxsize=1)
def get_session_factory():
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session | None, None, None]:
    try:
        session_factory = get_session_factory()
    except RuntimeError:
        yield None
        return
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def check_database() -> bool:
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
