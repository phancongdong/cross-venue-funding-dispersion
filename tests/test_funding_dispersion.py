"""Unit tests for Cross-Venue Funding Dispersion Strategy."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure package root is in sys.path
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

import numpy as np
import pandas as pd
import pytest

from src.models import VenueSeries, Candidate, PairTarget
from src.config import get_candidate_grid
from src.data_loader import parse_funding_timestamps
from src.signal_engine import target_for_decision, interval_rate_sum
from src.simulator import transition_actions, build_strategy_path, replay_strategy_path
from src.analytics import bootstrap_probability_positive


def make_synthetic_series(
    venue: str, timestamps: list[str], rates: list[float]
) -> VenueSeries:
    """Helper to create synthetic funding rate series for testing."""
    parsed = pd.to_datetime(timestamps, utc=True)
    ts_ns = np.asarray([ts.value for ts in parsed], dtype=np.int64)
    rate_arr = np.asarray(rates, dtype=float)
    return VenueSeries(
        symbol="TESTUSDT",
        venue=venue,
        path=Path(f"{venue}.parquet"),
        timestamps_ns=ts_ns,
        rates=rate_arr,
        prefix_rates=np.concatenate(([0.0], np.cumsum(rate_arr))),
        rows=len(rate_arr),
        first=parsed[0],
        last=parsed[-1],
        sha256="synthetic",
    )


def test_candidate_grid() -> None:
    grid = get_candidate_grid()
    assert len(grid) == 12
    assert {c.lookback_days for c in grid} == {1, 3, 7, 14}
    assert {c.threshold_bps_per_day for c in grid} == {0.0, 2.0, 5.0}


def test_timestamp_parser() -> None:
    raw = ["2023-05-12T00:00:00.048000+00:00", "2023-06-29T16:00:00+00:00"]
    parsed = parse_funding_timestamps(raw)
    assert len(parsed) == 2
    assert str(parsed.tz) == "UTC"


def test_point_in_time_causality() -> None:
    decision = pd.Timestamp("2025-01-02T00:00:00Z")
    low = make_synthetic_series(
        "venue_a",
        [
            "2025-01-01T00:00:00Z",
            "2025-01-01T08:00:00Z",
            "2025-01-01T16:00:00Z",
            "2025-01-02T00:00:00Z",  # exact decision time -> should be excluded by strictly-before rule
        ],
        [-0.0001, -0.0001, -0.0001, 0.50],
    )
    high = make_synthetic_series(
        "venue_b",
        [
            "2025-01-01T00:00:00Z",
            "2025-01-01T08:00:00Z",
            "2025-01-01T16:00:00Z",
            "2025-01-02T00:00:00Z",
        ],
        [0.0001, 0.0001, 0.0001, -0.50],
    )

    target, audit = target_for_decision(
        {"venue_a": low, "venue_b": high}, decision, Candidate(1, 0.0)
    )

    assert target is not None
    assert target.long_venue == "venue_a"
    assert target.short_venue == "venue_b"
    assert np.isclose(target.forecast_bps_per_day, 6.0)
    assert pd.Timestamp(audit["latest_signal_event_time"]) < decision


def test_staleness_and_threshold_guards() -> None:
    decision = pd.Timestamp("2025-01-02T00:00:00Z")
    fresh = make_synthetic_series(
        "fresh",
        ["2025-01-01T08:00:00Z", "2025-01-01T16:00:00Z"],
        [0.00005, 0.00005],
    )
    stale = make_synthetic_series(
        "stale",
        ["2024-12-31T08:00:00Z", "2024-12-31T16:00:00Z"],
        [-0.00005, -0.00005],
    )

    # 1. Staleness test
    target, audit = target_for_decision(
        {"fresh": fresh, "stale": stale}, decision, Candidate(3, 0.0)
    )
    assert target is None
    assert audit["reason"] == "INSUFFICIENT_FRESH_VENUES"

    # 2. Threshold test
    second = make_synthetic_series(
        "second",
        ["2025-01-01T08:00:00Z", "2025-01-01T16:00:00Z"],
        [0.00004, 0.00004],
    )
    target2, audit2 = target_for_decision(
        {"fresh": fresh, "second": second}, decision, Candidate(1, 5.0)
    )
    assert target2 is None
    assert audit2["reason"] == "BELOW_THRESHOLD"


def test_transition_leg_counting() -> None:
    p1 = PairTarget("bybit", "okx", 5.0)
    p1_same = PairTarget("bybit", "okx", 10.0)
    p1_flipped = PairTarget("okx", "bybit", 5.0)
    p1_one_changed = PairTarget("bybit", "hyperliquid", 5.0)

    assert transition_actions(None, p1) == (0, 2)
    assert transition_actions(p1, None) == (2, 0)
    assert transition_actions(p1, p1_same) == (0, 0)
    assert transition_actions(p1, p1_flipped) == (2, 2)
    assert transition_actions(p1, p1_one_changed) == (1, 1)


def test_funding_accounting_simulation() -> None:
    ts = [
        "2025-01-01T00:00:00Z",
        "2025-01-01T08:00:00Z",
        "2025-01-01T16:00:00Z",
        "2025-01-02T00:00:00Z",
        "2025-01-02T08:00:00Z",
        "2025-01-02T16:00:00Z",
        "2025-01-03T00:00:00Z",
    ]
    low = make_synthetic_series("low", ts, [-0.0001, -0.0001, -0.0001, 0.0, 0.0, 0.0, 0.0])
    high = make_synthetic_series("high", ts, [0.0001, 0.0001, 0.0001, 0.001, 0.001, 0.001, 0.001])

    start = pd.Timestamp("2025-01-02T00:00:00Z")
    end = pd.Timestamp("2025-01-04T00:00:00Z")
    path = build_strategy_path("TESTUSDT", {"low": low, "high": high}, Candidate(1, 0.0), start, end)

    normal_res = replay_strategy_path(path, 0.0005)
    stress_res = replay_strategy_path(path, 0.0010)

    assert normal_res["metrics"]["gross_funding_pnl_vnd"] > 0
    assert stress_res["metrics"]["pnl_vnd"] < normal_res["metrics"]["pnl_vnd"]
    # Due to compounding equity path, stress fees are approximately 2x normal fees
    assert stress_res["metrics"]["fees_vnd"] == pytest.approx(normal_res["metrics"]["fees_vnd"] * 2.0, rel=1e-2)


def test_bootstrap_reproducibility() -> None:
    data = [1.5, -0.8, 2.3, 0.4, -0.1]
    res1 = bootstrap_probability_positive(data, samples=1000, seed=42)
    res2 = bootstrap_probability_positive(data, samples=1000, seed=42)
    assert res1 == res2
    assert 0.0 <= res1["probability_mean_positive"] <= 1.0
