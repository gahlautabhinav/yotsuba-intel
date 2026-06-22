from __future__ import annotations

import time
from typing import Optional

import requests

from pivot.platforms.base import BasePivot, PivotData


class RedditPivot(BasePivot):
    PLATFORM = "reddit"
    RATE_LIMIT = 2.0

    def fetch(self, handle: str) -> tuple[str, Optional[PivotData]]:
        time.sleep(self.RATE_LIMIT)

        try:
            resp = requests.get(
                f"https://www.reddit.com/user/{handle}/about.json",
                headers={"User-Agent": "yotsuba-intel/1.0"},
                timeout=10,
            )
        except Exception:
            return "failed", None

        if resp.status_code in (403, 429):
            return "blocked", None
        if resp.status_code == 404:
            return "no_content", None
        if resp.status_code != 200:
            return "failed", None

        try:
            body = resp.json()
        except Exception:
            return "failed", None

        data_section = body.get("data", {})
        if not data_section:
            return "no_content", None

        pivot_data = PivotData(
            extra={
                "link_karma": data_section.get("link_karma"),
                "comment_karma": data_section.get("comment_karma"),
                "created_utc": data_section.get("created_utc"),
            }
        )
        return "success", pivot_data
