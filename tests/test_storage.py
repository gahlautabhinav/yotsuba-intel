"""Integration tests for storage.Repository using in-memory SQLite."""
from __future__ import annotations

import pytest
from datetime import datetime


class TestThreads:
    def test_save_and_list_thread(self, repo):
        t = repo.save_thread(board="g", thread_no=12345, subject="test thread")
        threads = repo.list_threads()
        assert len(threads) == 1
        assert threads[0].board == "g"
        assert threads[0].thread_no == 12345

    def test_save_thread_upserts(self, repo):
        repo.save_thread(board="g", thread_no=1, subject="old")
        repo.save_thread(board="g", thread_no=1, subject="new")
        threads = repo.list_threads()
        assert len(threads) == 1
        assert threads[0].subject == "new"

    def test_get_thread_by_id(self, repo):
        saved = repo.save_thread(board="v", thread_no=99)
        fetched = repo.get_thread(saved.id)
        assert fetched is not None
        assert fetched.id == saved.id

    def test_get_nonexistent_thread_returns_none(self, repo):
        assert repo.get_thread(9999) is None


class TestPosts:
    def test_save_post_and_retrieve_by_thread(self, repo):
        thread = repo.save_thread(board="g", thread_no=1)
        repo.save_post(
            thread_id=thread.id,
            post_no=101,
            resto=0,
            posted_at=datetime(2024, 1, 1),
            name="Anonymous",
            body_text="hello world",
            has_file=False,
        )
        posts = repo.get_posts_by_thread(thread.id)
        assert len(posts) == 1
        assert posts[0].post_no == 101
        assert posts[0].body_text == "hello world"

    def test_multiple_posts_same_thread(self, repo):
        thread = repo.save_thread(board="g", thread_no=2)
        for i in range(3):
            repo.save_post(
                thread_id=thread.id, post_no=200 + i,
                resto=0, posted_at=datetime(2024, 1, 1),
                name="Anon", body_text=f"post {i}", has_file=False,
            )
        posts = repo.get_posts_by_thread(thread.id)
        assert len(posts) == 3


class TestSocialLinks:
    def test_save_and_retrieve_pending_link(self, repo):
        thread = repo.save_thread(board="g", thread_no=3)
        post = repo.save_post(
            thread_id=thread.id, post_no=1, resto=0,
            posted_at=datetime(2024, 1, 1), name="Anon",
            body_text="github.com/user", has_file=False,
        )
        repo.save_social_link(
            post_id=post.id,
            platform="github",
            raw_url="https://github.com/user",
            handle="user",
            extraction_confidence=0.9,
            identity_weight=0.8,
            confidence=0.72,
        )
        links = repo.get_pending_links()
        assert len(links) == 1
        assert links[0].platform == "github"
        assert links[0].handle == "user"


class TestTripcodes:
    def test_upsert_and_list_tripcode(self, repo):
        repo.upsert_tripcode("!TestTrip123", "regular")
        trips = repo.list_tripcodes()
        assert len(trips) == 1
        assert trips[0].trip == "!TestTrip123"
        assert trips[0].trip_strength == "regular"

    def test_upsert_same_trip_twice_no_duplicate(self, repo):
        repo.upsert_tripcode("!UniqueTrip", "secure")
        repo.upsert_tripcode("!UniqueTrip", "secure")
        trips = repo.list_tripcodes()
        assert len(trips) == 1


class TestEmails:
    def test_save_email_and_retrieve_by_thread(self, repo):
        thread = repo.save_thread(board="g", thread_no=10)
        post = repo.save_post(
            thread_id=thread.id, post_no=1, resto=0,
            posted_at=datetime(2024, 1, 1), name="Anon",
            body_text="contact@example.com", has_file=False,
        )
        repo.save_email(post_id=post.id, email="contact@example.com", source="body")
        emails = repo.get_emails_by_thread(thread.id)
        assert len(emails) == 1
        assert emails[0].email == "contact@example.com"
