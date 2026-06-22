"""Cross-thread image correlation via MD5 reuse analysis."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from storage.engine import init_db
from storage.repository import Repository


@dataclass
class PostRef:
    source: str          # "local" or "4plebs" / "desuarchive" / "warosu"
    board: str
    thread_no: int
    post_no: int
    posted_at: Optional[datetime]
    name: Optional[str]
    trip: Optional[str]
    archive_url: Optional[str]


def correlate_md5(file_md5: str) -> dict:
    """
    Find all posts that used a specific file MD5 (image reuse analysis).

    Returns:
        {
            "file_md5": str,
            "post_refs": list[PostRef],
            "post_count": int,
            "board_count": int,
            "has_tripcode_match": bool,
            "confidence": float,
            "correlation_type": str,      # "strong" / "moderate" / "weak" / "meme_discard"
            "is_likely_meme": bool,
            "evidence": list[str],
        }
    """
    init_db()
    repo = Repository()

    # Query local posts
    local_posts = repo.get_posts_by_md5(file_md5)
    archive_posts = repo.get_archive_posts_by_md5(file_md5)

    # Build PostRef list
    refs: list[PostRef] = []

    for p in local_posts:
        # Get board from thread relationship — fetch thread to get board
        board = ""
        thread = repo.get_thread(p.thread_id)
        if thread:
            board = thread.board or ""
        refs.append(PostRef(
            source="local",
            board=board,
            thread_no=thread.thread_no if thread else 0,
            post_no=p.post_no,
            posted_at=p.posted_at,
            name=p.name,
            trip=p.trip,
            archive_url=None,
        ))

    for ap in archive_posts:
        refs.append(PostRef(
            source=ap.source,
            board=ap.board or "",
            thread_no=ap.thread_no,
            post_no=ap.post_no,
            posted_at=ap.posted_at,
            name=ap.name,
            trip=ap.trip,
            archive_url=ap.archive_url,
        ))

    post_count = len(refs)
    boards = list(set(r.board for r in refs if r.board))
    board_count = len(boards)
    has_tripcode_match = False
    is_likely_meme = False
    evidence: list[str] = []

    # Meme discard threshold
    if post_count > 30:
        is_likely_meme = True
        confidence = 0.05
        correlation_type = "meme_discard"
        evidence.append(f"High reuse count ({post_count} posts) — likely meme/template image")
    else:
        # Confidence scoring
        score = 0.0

        # Tripcode match across posts
        trips = [r.trip for r in refs if r.trip]
        if len(set(trips)) == 1 and len(trips) >= 2:
            score += 0.70
            evidence.append(f"Same tripcode '{trips[0]}' across {len(trips)} posts")
            has_tripcode_match = True

        # Same name (non-Anonymous)
        names = [r.name for r in refs if r.name and r.name != "Anonymous"]
        if len(set(names)) == 1 and len(names) >= 2:
            score += 0.25
            evidence.append(f"Same name '{names[0]}' across {len(names)} posts")

        # Low count bonus (2-5 posts = rare image)
        if 2 <= len(refs) <= 5:
            score += 0.20
            evidence.append(f"Rare image: only {len(refs)} uses")

        # Tight temporal cluster
        datetimes = [r.posted_at for r in refs if r.posted_at]
        if len(datetimes) >= 2:
            span_days = (max(datetimes) - min(datetimes)).days
            if span_days <= 7:
                score += 0.15
                evidence.append(f"Tight temporal cluster: {span_days} days")

        # Cross-board (2-4 boards = intentional poster, not viral)
        if 2 <= len(boards) <= 4:
            score += 0.10
            evidence.append(f"Posted across {len(boards)} boards: {', '.join(boards)}")

        # Classify
        if score >= 0.70:
            correlation_type = "strong"
        elif score >= 0.40:
            correlation_type = "moderate"
        else:
            correlation_type = "weak"

        confidence = min(1.0, score)

    # Save to DB
    repo.save_md5_correlation(
        file_md5=file_md5,
        post_count=post_count,
        board_count=board_count,
        has_tripcode_match=has_tripcode_match,
        confidence=confidence,
        correlation_type=correlation_type,
        is_likely_meme=is_likely_meme,
        evidence_json=json.dumps(evidence),
    )

    return {
        "file_md5": file_md5,
        "post_refs": refs,
        "post_count": post_count,
        "board_count": board_count,
        "has_tripcode_match": has_tripcode_match,
        "confidence": confidence,
        "correlation_type": correlation_type,
        "is_likely_meme": is_likely_meme,
        "evidence": evidence,
    }
