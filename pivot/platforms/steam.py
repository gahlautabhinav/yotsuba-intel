from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from typing import Optional

import requests

from pivot.platforms.base import BasePivot, PivotData


class SteamPivot(BasePivot):
    PLATFORM = "steam"
    RATE_LIMIT = 2.0

    def fetch(self, handle: str) -> tuple[str, Optional[PivotData]]:
        time.sleep(self.RATE_LIMIT)

        try:
            resp = requests.get(
                f"https://steamcommunity.com/id/{handle}/?xml=1",
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
            root = ET.fromstring(resp.text)
        except ET.ParseError:
            return "failed", None

        # Check for error
        error_elem = root.find("error")
        if error_elem is not None:
            return "no_content", None

        real_name = root.findtext("realname")
        steam_id64 = root.findtext("steamID64")
        location = root.findtext("location")
        avatar = root.findtext("avatarIcon")

        pivot_data = PivotData(
            real_name=real_name if real_name else None,
            location=location if location else None,
            avatar_url=avatar if avatar else None,
            extra={
                "steamID64": steam_id64,
                "avatar": avatar,
            },
        )
        return "success", pivot_data
