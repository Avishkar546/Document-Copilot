"""SQLAlchemy engine and session factory for direct Postgres access."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine, _session_factory
    if _engine is None:
        _engine = create_engine(settings.sqlalchemy_app_database_url)
        _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


@contextmanager
def get_session(user_id: uuid.UUID) -> Iterator[Session]:
    if _session_factory is None:
        get_engine()
    assert _session_factory is not None
    session = _session_factory()
    try:
        with session.begin():
            session.execute(text("SET LOCAL ROLE document_copilot_app"))
            session.execute(
                text("SELECT set_config('request.jwt.claim.sub', :user_id, true)"),
                {"user_id": str(user_id)},
            )
            yield session
    finally:
        session.close()
