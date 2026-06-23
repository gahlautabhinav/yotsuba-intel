"""Tests for analysis.temporal_profiler.infer_timezone."""
from __future__ import annotations

import pytest
from datetime import datetime

from analysis.temporal_profiler import infer_timezone


def _hours(*hours: int) -> list[datetime]:
    """Build datetime list where each value has the given UTC hour."""
    return [datetime(2024, 1, 1, h, 0, 0) for h in hours]


class TestInsufficientData:
    def test_fewer_than_5_returns_unknown(self):
        result = infer_timezone(_hours(1, 2, 3, 4))
        assert result["timezone_guess"] == "Unknown"
        assert result["confidence"] == 0.0
        assert result["warning"] is not None

    def test_zero_posts_returns_unknown(self):
        result = infer_timezone([])
        assert result["timezone_guess"] == "Unknown"

    def test_exactly_5_posts_proceeds(self):
        result = infer_timezone(_hours(20, 20, 20, 20, 20))
        assert result["timezone_guess"] != "Unknown"


class TestHistogram:
    def test_histogram_has_24_buckets(self):
        result = infer_timezone(_hours(0, 1, 2, 3, 4, 5))
        assert len(result["histogram"]) == 24

    def test_histogram_counts_match_input(self):
        result = infer_timezone(_hours(10, 10, 10, 10, 10))
        assert result["histogram"][10] == 5

    def test_peak_hour_utc_is_correct(self):
        result = infer_timezone(_hours(15, 15, 15, 15, 15))
        assert result["peak_hour_utc"] == 15


class TestConfidence:
    def test_concentrated_activity_high_confidence(self):
        # All posts at same hour → max concentration
        result = infer_timezone(_hours(*([21] * 10)))
        assert result["confidence"] >= 0.8

    def test_spread_activity_low_confidence(self):
        # Spread across all 24 hours (repeat each hour once = 24 posts, spread)
        spread = list(range(24))
        result = infer_timezone([datetime(2024, 1, 1, h) for h in spread])
        assert result["confidence"] < 0.5
        assert result["warning"] is not None

    def test_confidence_capped_at_1(self):
        result = infer_timezone(_hours(*([21] * 20)))
        assert result["confidence"] <= 1.0


class TestTimezoneOffset:
    def test_peak_at_21_utc_gives_utc0(self):
        # local_peak=21, peak_hour=21 → offset = 21-21 = 0
        result = infer_timezone(_hours(*([21] * 10)))
        assert result["timezone_guess"] == "UTC+0"

    def test_offset_format_positive(self):
        # Peak at 16 UTC → offset = 21-16 = +5 → UTC+5
        result = infer_timezone(_hours(*([16] * 10)))
        assert result["timezone_guess"] == "UTC+5"

    def test_offset_format_negative(self):
        # Peak at 23 UTC → offset = 21-23 = -2 → UTC-2
        result = infer_timezone(_hours(*([23] * 10)))
        assert result["timezone_guess"] == "UTC-2"
