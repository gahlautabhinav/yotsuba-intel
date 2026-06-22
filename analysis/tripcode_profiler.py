"""Aggregate identity profiling for tripcodes from local DB and archive posts."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from analysis.temporal_profiler import infer_timezone
from storage.engine import init_db
from storage.repository import Repository


@dataclass
class TripcodeProfile:
    trip: str
    trip_strength: str              # "regular" or "secure"
    post_count: int
    archive_post_count: int
    boards: list[str]
    countries: list[str]
    name_variants: list[str]
    first_seen: Optional[datetime]
    last_seen: Optional[datetime]
    social_links: list[dict]        # [{platform, handle, confidence}]
    emails: list[str]
    pgp_fingerprints: list[str]
    timezone_guess: str
    timezone_confidence: float
    timezone_histogram: list[int]   # 24 values
    timezone_warning: Optional[str]
    # Computed by profiler
    active_boards: list[str]        # sorted by post count desc
    post_datetimes: list[datetime]  # all post timestamps for timeline


def profile_trip(trip: str) -> TripcodeProfile:
    """Build full identity profile for a tripcode from local DB + archive posts."""
    init_db()
    repo = Repository()

    # Get the DB tripcode record
    tripcode_obj = repo.get_tripcode(trip)
    if tripcode_obj is None:
        raise ValueError(f"Tripcode '{trip}' not found in local database.")

    # Get local posts and archive posts
    local_posts = repo.get_posts_by_trip(trip)
    archive_posts = repo.get_archive_posts_by_trip(trip)

    # Collect all datetimes for timezone inference
    datetimes: list[datetime] = (
        [p.posted_at for p in local_posts if p.posted_at]
        + [ap.posted_at for ap in archive_posts if ap.posted_at]
    )

    # Run timezone inference
    tz_result = infer_timezone(datetimes)

    # Parse JSON fields from the Tripcode row
    boards: list[str] = json.loads(tripcode_obj.boards_seen or "[]")
    countries: list[str] = json.loads(tripcode_obj.countries_seen or "[]")
    name_variants: list[str] = json.loads(tripcode_obj.name_variants or "[]")
    emails: list[str] = json.loads(tripcode_obj.emails_found or "[]")

    # Get social links for all local posts
    post_ids = [p.id for p in local_posts]
    raw_links = repo.get_links_by_post_ids(post_ids) if post_ids else []
    social_links = [
        {
            "platform": lnk.platform,
            "handle": lnk.handle,
            "confidence": lnk.confidence,
        }
        for lnk in raw_links
    ]

    # Get PGP fingerprints for all local posts
    raw_pgp = repo.get_pgp_keys_by_post_ids(post_ids) if post_ids else []
    pgp_fingerprints = [k.fingerprint for k in raw_pgp]

    # Compute active_boards: sort boards by post frequency among local posts
    board_counts: dict[str, int] = {}
    for p in local_posts:
        # Need board from thread; use boards_seen from tripcode as fallback
        pass

    # For active_boards, use the boards list (already ordered by insertion/uniqueness)
    # Build a richer count from archive posts too
    all_board_list: list[str] = []
    for ap in archive_posts:
        if ap.board:
            all_board_list.append(ap.board)
    for b in boards:
        if b not in board_counts:
            board_counts[b] = 0
    for b in all_board_list:
        board_counts[b] = board_counts.get(b, 0) + 1

    active_boards = sorted(board_counts.keys(), key=lambda b: board_counts[b], reverse=True)
    if not active_boards:
        active_boards = list(boards)

    # Save timezone back to DB
    repo.update_tripcode_timezone(trip, tz_result)

    return TripcodeProfile(
        trip=trip,
        trip_strength=tripcode_obj.trip_strength or "regular",
        post_count=tripcode_obj.post_count or 0,
        archive_post_count=len(archive_posts),
        boards=boards,
        countries=countries,
        name_variants=name_variants,
        first_seen=tripcode_obj.first_seen_at,
        last_seen=tripcode_obj.last_seen_at,
        social_links=social_links,
        emails=emails,
        pgp_fingerprints=pgp_fingerprints,
        timezone_guess=tz_result["timezone_guess"],
        timezone_confidence=tz_result["confidence"],
        timezone_histogram=tz_result["histogram"],
        timezone_warning=tz_result.get("warning"),
        active_boards=active_boards,
        post_datetimes=datetimes,
    )
