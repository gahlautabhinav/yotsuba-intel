from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PivotData:
    real_name: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    linked_accounts: dict[str, str] = field(default_factory=dict)
    extra: dict = field(default_factory=dict)


class BasePivot(ABC):
    PLATFORM: str        # e.g. "github"
    RATE_LIMIT: float    # seconds between requests (default 1.0)

    @abstractmethod
    def fetch(self, handle: str) -> tuple[str, PivotData | None]:
        """Return (status, data).
        status: 'success' | 'failed' | 'blocked' | 'no_content'
        """
        ...
