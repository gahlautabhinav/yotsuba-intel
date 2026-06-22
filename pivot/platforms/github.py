from __future__ import annotations

import time
from typing import Optional

import requests

from pivot.platforms.base import BasePivot, PivotData


class GitHubPivot(BasePivot):
    PLATFORM = "github"
    RATE_LIMIT = 1.0

    def fetch(self, handle: str) -> tuple[str, Optional[PivotData]]:
        time.sleep(self.RATE_LIMIT)

        from config.settings import settings

        headers: dict[str, str] = {}
        if settings.github_token:
            headers["Authorization"] = f"token {settings.github_token}"

        try:
            resp = requests.get(
                f"https://api.github.com/users/{handle}",
                headers=headers,
                timeout=10,
            )
        except Exception as e:
            return "failed", None

        if resp.status_code in (403, 429):
            return "blocked", None
        if resp.status_code == 404:
            return "no_content", None
        if resp.status_code != 200:
            return "failed", None

        try:
            user = resp.json()
        except Exception:
            return "failed", None

        # Fetch commit emails from events
        commit_emails: list[str] = []
        try:
            ev_resp = requests.get(
                f"https://api.github.com/users/{handle}/events?per_page=100",
                headers=headers,
                timeout=10,
            )
            if ev_resp.status_code == 200:
                events = ev_resp.json()
                seen: set[str] = set()
                for event in events:
                    if event.get("type") == "PushEvent":
                        for commit in event.get("payload", {}).get("commits", []):
                            email = commit.get("author", {}).get("email", "")
                            if email and email not in seen:
                                seen.add(email)
                                commit_emails.append(email)
        except Exception:
            pass

        linked: dict[str, str] = {}
        tw = user.get("twitter_username")
        if tw:
            linked["twitter"] = tw

        data = PivotData(
            real_name=user.get("name"),
            email=user.get("email"),
            location=user.get("location"),
            bio=user.get("bio"),
            avatar_url=user.get("avatar_url"),
            linked_accounts=linked,
            extra={
                "company": user.get("company"),
                "blog": user.get("blog"),
                "commit_emails": commit_emails,
            },
        )
        return "success", data
