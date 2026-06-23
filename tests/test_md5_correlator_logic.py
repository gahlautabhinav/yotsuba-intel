"""Tests for MD5 correlator scoring logic."""
from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from analysis.md5_correlator import correlate_md5, PostRef


def _ref(
    trip=None, name="Anonymous", board="g",
    thread_no=1, post_no=1,
    posted_at=None, source="local", archive_url=None,
) -> PostRef:
    return PostRef(
        source=source, board=board, thread_no=thread_no,
        post_no=post_no, posted_at=posted_at, name=name,
        trip=trip, archive_url=archive_url,
    )


def _mock_repo(local_posts=None, archive_posts=None, thread=None):
    """Return a mock Repository that yields controlled data."""
    repo = MagicMock()
    repo.get_posts_by_md5.return_value = local_posts or []
    repo.get_archive_posts_by_md5.return_value = archive_posts or []
    repo.get_thread.return_value = thread
    repo.save_md5_correlation.return_value = None
    return repo


class TestMemeDiscard:
    def test_more_than_30_posts_is_meme(self):
        # Build 31 mock Post objects
        posts = []
        for i in range(31):
            p = MagicMock()
            p.post_no = i
            p.posted_at = None
            p.name = "Anonymous"
            p.trip = None
            posts.append(p)

        thread_mock = MagicMock()
        thread_mock.board = "g"
        thread_mock.thread_no = 1

        repo = _mock_repo(local_posts=posts, thread=thread_mock)

        with patch("analysis.md5_correlator.Repository", return_value=repo), \
             patch("analysis.md5_correlator.init_db"):
            result = correlate_md5("testmd5==")

        assert result["is_likely_meme"] is True
        assert result["confidence"] == pytest.approx(0.05)
        assert result["correlation_type"] == "meme_discard"

    def test_exactly_30_posts_not_meme(self):
        posts = []
        for i in range(30):
            p = MagicMock()
            p.post_no = i
            p.posted_at = None
            p.name = "Anonymous"
            p.trip = None
            posts.append(p)

        thread_mock = MagicMock()
        thread_mock.board = "g"
        thread_mock.thread_no = 1

        repo = _mock_repo(local_posts=posts, thread=thread_mock)

        with patch("analysis.md5_correlator.Repository", return_value=repo), \
             patch("analysis.md5_correlator.init_db"):
            result = correlate_md5("testmd5==")

        assert result["is_likely_meme"] is False


class TestScoringLogic:
    def _run(self, posts_data: list[dict]) -> dict:
        """Helper: build mock Posts and run correlate_md5."""
        local_posts = []
        thread_mock = MagicMock()
        thread_mock.board = "g"
        thread_mock.thread_no = 99

        for d in posts_data:
            p = MagicMock()
            p.post_no = d.get("post_no", 1)
            p.posted_at = d.get("posted_at")
            p.name = d.get("name", "Anonymous")
            p.trip = d.get("trip")
            local_posts.append(p)

        repo = _mock_repo(local_posts=local_posts, thread=thread_mock)

        with patch("analysis.md5_correlator.Repository", return_value=repo), \
             patch("analysis.md5_correlator.init_db"):
            return correlate_md5("testmd5==")

    def test_tripcode_match_gives_strong(self):
        result = self._run([
            {"post_no": 1, "trip": "!SameTrip", "name": "Anon"},
            {"post_no": 2, "trip": "!SameTrip", "name": "Anon"},
        ])
        assert result["has_tripcode_match"] is True
        assert result["correlation_type"] == "strong"
        assert result["confidence"] >= 0.70

    def test_different_tripcodes_no_match(self):
        result = self._run([
            {"post_no": 1, "trip": "!TripA", "name": "Anon"},
            {"post_no": 2, "trip": "!TripB", "name": "Anon"},
        ])
        assert result["has_tripcode_match"] is False

    def test_rare_image_2_posts_gives_bonus(self):
        result = self._run([
            {"post_no": 1, "name": "Anonymous"},
            {"post_no": 2, "name": "Anonymous"},
        ])
        # 2 posts → rare bonus 0.20 → confidence = 0.20 → weak
        assert result["confidence"] == pytest.approx(0.20)
        assert any("Rare image" in e for e in result["evidence"])

    def test_single_post_no_rare_bonus(self):
        result = self._run([{"post_no": 1, "name": "Anonymous"}])
        # 1 post → no rare bonus, no other signals → confidence = 0
        assert result["confidence"] == pytest.approx(0.0)
        assert result["correlation_type"] == "weak"

    def test_temporal_cluster_adds_bonus(self):
        d1 = datetime(2024, 1, 1, 12, 0)
        d2 = datetime(2024, 1, 3, 12, 0)  # 2 days apart
        result = self._run([
            {"post_no": 1, "posted_at": d1, "name": "Anonymous"},
            {"post_no": 2, "posted_at": d2, "name": "Anonymous"},
        ])
        # Rare (2 posts, +0.20) + temporal cluster ≤7 days (+0.15) = 0.35
        assert result["confidence"] == pytest.approx(0.35)
        assert any("cluster" in e for e in result["evidence"])
