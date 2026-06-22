from __future__ import annotations

import re
import time
from typing import Optional

import requests

from pivot.platforms.base import BasePivot, PivotData

# Match lines like: uid:Real Name <email@example.com>:...
# or armored UID comment lines
UID_EMAIL_RE = re.compile(r"<([^>]+@[^>]+)>")
UID_NAME_RE = re.compile(r"uid\s*[:\s]+([^<\n]+?)\s*<")


class PgpPivot(BasePivot):
    PLATFORM = "pgp"
    RATE_LIMIT = 1.0

    def fetch(self, handle: str) -> tuple[str, Optional[PivotData]]:
        time.sleep(self.RATE_LIMIT)

        fingerprint = handle.strip().upper().replace(" ", "").replace("0x", "").replace("0X", "")

        try:
            resp = requests.get(
                f"https://keys.openpgp.org/vks/v1/by-fingerprint/{fingerprint}",
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

        emails_found = UID_EMAIL_RE.findall(text)
        names_found = UID_NAME_RE.findall(text)

        first_email = emails_found[0] if emails_found else None
        first_name = names_found[0].strip() if names_found else None

        pivot_data = PivotData(
            real_name=first_name,
            email=first_email,
            extra={
                "fingerprint": fingerprint,
                "uid_count": len(emails_found),
            },
        )
        return "success", pivot_data
