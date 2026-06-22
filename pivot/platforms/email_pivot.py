from __future__ import annotations

import hashlib
import time
from typing import Optional

import requests

from pivot.platforms.base import BasePivot, PivotData


class EmailPivot(BasePivot):
    PLATFORM = "email"
    RATE_LIMIT = 1.5

    def fetch(self, handle: str) -> tuple[str, Optional[PivotData]]:
        time.sleep(self.RATE_LIMIT)

        from config.settings import settings

        email = handle.strip().lower()
        md5_hash = hashlib.md5(email.encode()).hexdigest()

        real_name: Optional[str] = None
        linked_accounts: dict[str, str] = {}
        breach_count: Optional[int] = None
        breach_names: list[str] = []
        got_data = False

        # --- Gravatar lookup ---
        try:
            g_resp = requests.get(
                f"https://www.gravatar.com/{md5_hash}.json",
                timeout=10,
            )
            if g_resp.status_code == 200:
                g_body = g_resp.json()
                entries = g_body.get("entry", [])
                if entries:
                    entry = entries[0]
                    real_name = entry.get("displayName")
                    for acc in entry.get("accounts", []):
                        shortname = acc.get("shortname")
                        url = acc.get("url")
                        if shortname and url:
                            linked_accounts[shortname] = url
                    got_data = True
        except Exception:
            pass

        # --- HIBP lookup (optional) ---
        if settings.hibp_api_key:
            try:
                h_resp = requests.get(
                    f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                    headers={"hibp-api-key": settings.hibp_api_key},
                    timeout=10,
                )
                if h_resp.status_code == 200:
                    breaches = h_resp.json()
                    breach_count = len(breaches)
                    breach_names = [b["Name"] for b in breaches]
                    got_data = True
                elif h_resp.status_code == 404:
                    breach_count = 0
                    got_data = True
            except Exception:
                pass

        if not got_data:
            return "no_content", None

        pivot_data = PivotData(
            real_name=real_name,
            linked_accounts=linked_accounts,
            extra={
                "breach_count": breach_count,
                "breach_names": breach_names,
            },
        )
        return "success", pivot_data
