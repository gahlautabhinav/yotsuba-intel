import json
import pytest
from pathlib import Path
from scraper.post_parser import parse_thread

FIXTURE = Path(__file__).parent / "fixtures" / "sample_thread.json"


def test_parse_returns_thread_and_posts():
    raw = json.loads(FIXTURE.read_text())
    thread, posts = parse_thread("g", raw)
    assert thread["board"] == "g"
    assert thread["thread_no"] > 0
    assert len(posts) > 0


def test_first_post_is_op():
    raw = json.loads(FIXTURE.read_text())
    _, posts = parse_thread("g", raw)
    assert posts[0]["resto"] == 0


def test_body_text_strips_html():
    raw = json.loads(FIXTURE.read_text())
    _, posts = parse_thread("g", raw)
    for p in posts:
        assert "<" not in p["body_text"]


def test_posted_at_is_datetime():
    from datetime import datetime
    raw = json.loads(FIXTURE.read_text())
    _, posts = parse_thread("g", raw)
    assert isinstance(posts[0]["posted_at"], datetime)
