"""Shared pytest fixtures — in-memory SQLite for all DB-touching tests."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

import storage.models  # noqa: F401 — registers all ORM models with Base
import storage.engine as _eng
from storage.engine import Base


@pytest.fixture()
def in_memory_engine(monkeypatch):
    """Create a fresh in-memory SQLite engine and patch the storage module globals."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=eng,
        expire_on_commit=False,
    )
    monkeypatch.setattr(_eng, "_engine", eng)
    monkeypatch.setattr(_eng, "_SessionLocal", session_factory)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def repo(in_memory_engine):
    """Return a Repository wired to the in-memory engine."""
    from storage.repository import Repository
    return Repository()
