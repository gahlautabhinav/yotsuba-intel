from __future__ import annotations

import re
import time
from typing import Optional

import requests

from pivot.platforms.base import BasePivot, PivotData

EMAIL_RE = re.compile(r"[\w.+\-]+@[\w\-]+\.[a-zA-Z]{2,}")
WINDOWS_USER_RE = re.compile(r"C:\\Users\\(\w+)\\")
PASTE_KEY_RE = re.compile(r"^[A-Za-z0-9]{8}$")


class PastebinPivot(BasePivot):
    PLATFORM = "pastebin"
    RATE_LIMIT = 1.0

    def fetch(self, handle: str) -> tuple[str, Optional[PivotData]]:
        time.sleep(self.RATE_LIMIT)

        # If it looks like a username, skip
        if handle.startswith("/u/") or not PASTE_KEY_RE.match(handle):
            return "no_content", None

        try:
            resp = requests.get(
                f"https://pastebin.com/raw/{handle}",
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

        text = resp.text
        emails_found = list(set(EMAIL_RE.findall(text)))
        users_found = list(set(WINDOWS_USER_RE.findall(text)))

        pivot_data = PivotData(
            extra={
                "emails_found": emails_found,
                "users_found": users_found,
                "raw_snippet": text[:500],
            }
        )
        return "success", pivot_data
