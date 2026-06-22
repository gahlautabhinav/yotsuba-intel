from __future__ import annotations

import re
import time
from typing import Optional

import requests

from pivot.platforms.base import BasePivot, PivotData

EMAIL_RE = re.compile(r"[\w.+\-]+@[\w\-]+\.[a-zA-Z]{2,}")
TITLE_RE = re.compile(r"<title[^>]*>([^<]+)</title>", re.IGNORECASE)
OG_TITLE_RE = re.compile(
    r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
OG_DESC_RE = re.compile(
    r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


class GenericPivot(BasePivot):
    PLATFORM = "generic"
    RATE_LIMIT = 1.0

    def fetch(self, handle: str) -> tuple[str, Optional[PivotData]]:
        time.sleep(self.RATE_LIMIT)

        url = handle if handle.startswith("http") else f"https://{handle}"

        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "yotsuba-intel/1.0"},
                timeout=10,
            )
        except Exception:
            return "failed", None

        if resp.status_code in (403, 429):
            return "blocked", None
        if resp.status_code >= 400:
            return "failed", None

        body = resp.text

        title_match = TITLE_RE.search(body)
        title = title_match.group(1).strip() if title_match else None

        og_title_match = OG_TITLE_RE.search(body)
        og_title = og_title_match.group(1).strip() if og_title_match else None

        og_desc_match = OG_DESC_RE.search(body)
        og_description = og_desc_match.group(1).strip() if og_desc_match else None

        emails_found = list(set(EMAIL_RE.findall(body)))

        pivot_data = PivotData(
            extra={
                "title": title,
                "og_title": og_title,
                "og_description": og_description,
                "emails_found": emails_found,
            }
        )
        return "success", pivot_data
