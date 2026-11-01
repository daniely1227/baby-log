"""Render hands the app a database address that starts with postgres:// or postgresql://.

The app has to rewrite it to postgresql+psycopg2:// so SQLAlchemy uses psycopg2, the
PostgreSQL driver in requirements.txt. Without this the live app crashed on start.
"""
from app import database_url


def test_render_database_url_uses_psycopg2(monkeypatch):
    for given in ("postgres://user:pw@host:5432/runlog", "postgresql://user:pw@host:5432/runlog"):
        monkeypatch.setenv("DATABASE_URL", given)
        assert database_url() == "postgresql+psycopg2://user:pw@host:5432/runlog"


def test_without_database_url_uses_local_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert database_url() == "sqlite:///runlog.db"
