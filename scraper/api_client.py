"""
4chan API client with token-bucket rate limiting and If-Modified-Since support.
"""
from __future__ import annotations

import re
import time
from typing import Optional

import requests

from config.settings import settings


class ChanAPIClient:
    BASE = "https://a.4cdn.org"

    # Token-bucket rate limiter state
    _BUCKET_CAPACITY = 1.0   # max tokens
    _REFILL_RATE = 1.0       # tokens per second

    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": settings.user_agent})

        # Token bucket
        self._tokens: float = self._BUCKET_CAPACITY
        self._last_refill: float = time.time()

        # If-Modified-Since / response cache
        self._last_modified: dict[tuple[str, int], str] = {}
        self._cached_response: dict[tuple[str, int], dict] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_thread_url(self, url: str) -> tuple[str, int]:
        """Parse a 4chan thread URL and return (board, thread_no).

        Accepts:
          https://boards.4chan.org/{board}/thread/{no}
          https://4chan.org/{board}/thread/{no}
        """
        pattern = re.compile(
            r'https?://(?:boards\.)?4chan(?:nel)?\.org/(\w+)/thread/(\d+)',
            re.I,
        )
        m = pattern.search(url)
        if not m:
            raise ValueError(f"Invalid 4chan thread URL: {url!r}")
        return m.group(1), int(m.group(2))

    def get_thread(self, board: str, thread_no: int) -> Optional[dict]:
        """Fetch thread JSON from 4chan API.

        Returns:
            dict   on 200 OK
            None   on 404 (thread deleted / archived)
        Raises:
            requests.HTTPError  for any other HTTP error
        """
        self._consume_token()

        key = (board, thread_no)
        url = f"{self.BASE}/{board}/thread/{thread_no}.json"

        headers: dict[str, str] = {}
        if key in self._last_modified:
            headers["If-Modified-Since"] = self._last_modified[key]

        resp = self._session.get(url, headers=headers, timeout=15)

        if resp.status_code == 200:
            data = resp.json()
            self._cached_response[key] = data
            lm = resp.headers.get("Last-Modified")
            if lm:
                self._last_modified[key] = lm
            return data

        if resp.status_code == 304:
            # Not modified — return cached response
            return self._cached_response.get(key)

        if resp.status_code == 404:
            return None

        resp.raise_for_status()
        return None  # unreachable, but satisfies type checker

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _consume_token(self) -> None:
        """Block until a token is available (1 req/sec rate limit)."""
        now = time.time()
        elapsed = now - self._last_refill
        self._tokens = min(
            self._BUCKET_CAPACITY,
            self._tokens + elapsed * self._REFILL_RATE,
        )
        self._last_refill = now

        if self._tokens < 1.0:
            sleep_time = (1.0 - self._tokens) / self._REFILL_RATE
            time.sleep(sleep_time)
            self._tokens = 0.0
        else:
            self._tokens -= 1.0
