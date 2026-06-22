from __future__ import annotations

import dataclasses
import json
from typing import Optional

from storage.engine import init_db
from storage.repository import Repository
from pivot.platforms.base import BasePivot, PivotData
from pivot.platforms.github import GitHubPivot
from pivot.platforms.reddit import RedditPivot
from pivot.platforms.keybase import KeybasePivot
from pivot.platforms.steam import SteamPivot
from pivot.platforms.pastebin import PastebinPivot
from pivot.platforms.email_pivot import EmailPivot
from pivot.platforms.pgp_keyserver import PgpPivot
from pivot.platforms.twitter import TwitterPivot
from pivot.platforms.telegram import TelegramPivot
from pivot.platforms.instagram import InstagramPivot
from pivot.platforms.generic import GenericPivot


PLATFORM_PRIORITY: dict[str, int] = {
    "pgp": 1,
    "keybase": 2,
    "github": 3,
    "email": 4,
    "steam": 5,
    "twitter": 6,
    "instagram": 7,
    "telegram": 8,
    "reddit": 9,
    "pastebin": 10,
    "generic": 11,
}

PLATFORM_MAP: dict[str, type[BasePivot]] = {
    "github": GitHubPivot,
    "reddit": RedditPivot,
    "keybase": KeybasePivot,
    "steam": SteamPivot,
    "pastebin": PastebinPivot,
    "email": EmailPivot,
    "pgp": PgpPivot,
    "twitter": TwitterPivot,
    "telegram": TelegramPivot,
    "instagram": InstagramPivot,
    "generic": GenericPivot,
}


def run_pivots(
    thread_id: Optional[int] = None,
    platforms: Optional[list[str]] = None,
) -> dict[str, int]:
    """Run pending pivots. Returns {"processed": N, "success": N, "failed": N, "skipped": N}"""
    init_db()
    repo = Repository()

    links = repo.get_pending_links()

    # Filter by thread if specified
    if thread_id is not None:
        posts = repo.get_posts_by_thread(thread_id)
        post_ids = {p.id for p in posts}
        links = [lk for lk in links if lk.post_id in post_ids]

    # Filter by platform
    if platforms:
        links = [lk for lk in links if lk.platform in platforms]

    # Sort by priority
    links.sort(key=lambda lk: PLATFORM_PRIORITY.get(lk.platform, 99))

    counts: dict[str, int] = {"processed": 0, "success": 0, "no_content": 0, "failed": 0, "skipped": 0}

    for lk in links:
        handle = lk.handle or lk.raw_url
        if not handle:
            counts["skipped"] += 1
            continue

        pivot_cls = PLATFORM_MAP.get(lk.platform)
        if pivot_cls is None:
            counts["skipped"] += 1
            continue

        error_msg: Optional[str] = None
        try:
            fetcher = pivot_cls()
            status, data = fetcher.fetch(handle)
        except Exception as e:
            status = "failed"
            data = None
            error_msg = str(e)

        profile_data: Optional[str] = None
        if data is not None:
            profile_data = json.dumps(dataclasses.asdict(data))

        repo.save_pivot_result(
            link_id=lk.id,
            status=status,
            profile_data=profile_data,
            raw_html_snippet=None,
            error=error_msg if status == "failed" else None,
        )

        counts["processed"] += 1
        if status == "success":
            counts["success"] += 1
        elif status in ("no_content", "blocked"):
            counts["no_content"] += 1
        else:
            counts["failed"] += 1

    return counts
