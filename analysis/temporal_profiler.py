"""Timezone inference from post timestamps via hourly histogram analysis."""
from __future__ import annotations

from datetime import datetime
from typing import Optional


def infer_timezone(post_datetimes: list[datetime]) -> dict:
    """
    Infer timezone from a list of UTC post datetimes using hourly histogram.

    Returns:
        {
            "timezone_guess": str,       # e.g. "UTC-5" or "Unknown"
            "confidence": float,         # 0.0-1.0
            "histogram": list[int],      # 24 hourly counts [hour0..hour23]
            "peak_hour_utc": int,        # hour 0-23 with most activity
            "warning": str | None,       # e.g. "insufficient data" or None
        }
    """
    if len(post_datetimes) < 5:
        return {
            "timezone_guess": "Unknown",
            "confidence": 0.0,
            "histogram": [0] * 24,
            "peak_hour_utc": 0,
            "warning": "insufficient data (< 5 posts)",
        }

    # Build hourly histogram
    histogram = [0] * 24
    for dt in post_datetimes:
        histogram[dt.hour] += 1

    # Find peak hour
    peak_hour = histogram.index(max(histogram))

    # Assume peak activity is around 9pm local time
    local_peak = 21
    utc_offset = local_peak - peak_hour

    # Normalize offset to range -12..+14
    while utc_offset < -12:
        utc_offset += 24
    while utc_offset > 14:
        utc_offset -= 24

    # Confidence based on concentration of activity
    total = sum(histogram)
    top3 = sum(sorted(histogram, reverse=True)[:3])
    concentration = top3 / total  # fraction of posts in top 3 hours
    confidence = min(1.0, concentration * 1.5)

    # Format timezone string
    timezone_guess = f"UTC{utc_offset:+d}"

    # Warning for low confidence
    warning: Optional[str] = None
    if confidence < 0.3:
        warning = "low confidence — activity spread across many hours"

    return {
        "timezone_guess": timezone_guess,
        "confidence": confidence,
        "histogram": histogram,
        "peak_hour_utc": peak_hour,
        "warning": warning,
    }
