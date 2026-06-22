from __future__ import annotations

import time
from typing import Optional

from pivot.platforms.base import BasePivot, PivotData


class TelegramPivot(BasePivot):
    PLATFORM = "telegram"
    RATE_LIMIT = 1.0

    def fetch(self, handle: str) -> tuple[str, Optional[PivotData]]:
        time.sleep(self.RATE_LIMIT)
        # No public API available — stub only
        return "no_content", None
