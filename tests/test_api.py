"""FastAPI route tests using TestClient + in-memory SQLite."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(in_memory_engine):
    """Return a TestClient with the app wired to in-memory DB."""
    from api.main import app
    with TestClient(app) as c:
        yield c


class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestStats:
    def test_stats_returns_counts(self, client):
        resp = client.get("/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "thread_count" in data
        assert "tripcode_count" in data
        assert data["thread_count"] == 0
        assert data["tripcode_count"] == 0


class TestThreadsRoute:
    def test_list_threads_empty(self, client):
        resp = client.get("/threads/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_nonexistent_thread_404(self, client):
        resp = client.get("/threads/9999")
        assert resp.status_code == 404


class TestScrapeRoute:
    def test_scrape_returns_started(self, client):
        resp = client.post("/scrape/", json={"url": "https://boards.4chan.org/g/thread/123456"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "started"

    def test_scrape_missing_url_422(self, client):
        resp = client.post("/scrape/", json={})
        assert resp.status_code == 422
