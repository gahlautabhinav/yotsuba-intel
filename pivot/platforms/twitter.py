from __future__ import annotations

import time
from typing import Optional

from pivot.platforms.base import BasePivot, PivotData


class TwitterPivot(BasePivot):
    PLATFORM = "twitter"
    RATE_LIMIT = 2.0

    def fetch(self, handle: str) -> tuple[str, Optional[PivotData]]:
        time.sleep(self.RATE_LIMIT)
        # Twitter API requires OAuth — stub only
        return "no_content", None
