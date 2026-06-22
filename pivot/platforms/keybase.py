from __future__ import annotations

import time
from typing import Optional

import requests

from pivot.platforms.base import BasePivot, PivotData


class KeybasePivot(BasePivot):
    PLATFORM = "keybase"
    RATE_LIMIT = 1.0

    def fetch(self, handle: str) -> tuple[str, Optional[PivotData]]:
        time.sleep(self.RATE_LIMIT)

        try:
            resp = requests.get(
                f"https://keybase.io/{handle}/_/api/1.0/user/lookup.json?username={handle}",
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

        them = body.get("them", [])
        if not them:
            return "no_content", None

        user = them[0]
        profile = user.get("profile", {}) or {}
        proofs = (
            user.get("proofs_summary", {}).get("all", []) or []
        )

        linked: dict[str, str] = {
            proof["proof_type"]: proof["nametag"]
            for proof in proofs
            if proof.get("proof_type") and proof.get("nametag")
        }

        pivot_data = PivotData(
            real_name=profile.get("full_name"),
            location=profile.get("location"),
            bio=profile.get("bio"),
            linked_accounts=linked,
        )
        return "success", pivot_data
