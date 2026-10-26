"""Signal generation and pair ranking engine for cross-venue funding dispersion."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .models import VenueSeries, Candidate, PairTarget
from .config import STALE_HOURS


def interval_rate_sum(series: VenueSeries, start_ns: int, end_ns: int) -> tuple[float, int]:
    """Compute the sum of funding rates and event count in [start_ns, end_ns] using binary search."""
    if series.rows == 0:
        return 0.0, 0
    left = int(np.searchsorted(series.timestamps_ns, start_ns, side="left"))
    right = int(np.searchsorted(series.timestamps_ns, end_ns, side="right"))
    if left >= right:
        return 0.0, 0
    total = float(series.prefix_rates[right] - series.prefix_rates[left])
    return total, right - left


def target_for_decision(
    venues: dict[str, VenueSeries],
    decision_time: pd.Timestamp,
    candidate: Candidate,
    stale_hours: float = STALE_HOURS,
) -> tuple[PairTarget | None, dict[str, Any]]:
    """Determine the optimal long/short venue pair at a decision timestamp.

    Guarantees strict point-in-time causality:
    - Uses only events published strictly before `decision_time`.
    - Enforces freshness: rejects venues whose latest event is older than `stale_hours`.
    - Selects the venue with the lowest trailing funding for Long.
    - Selects the venue with the highest trailing funding for Short.
    - Emits a signal only if the forecast spread meets or exceeds `candidate.threshold_bps_per_day`.
    """
    decision_ns = int(decision_time.value)
    lookback_start_ns = int((decision_time - pd.Timedelta(days=candidate.lookback_days)).value)
    stale_cutoff_ns = int((decision_time - pd.Timedelta(hours=stale_hours)).value)

    fresh_metrics: dict[str, dict[str, Any]] = {}

    for venue, series in venues.items():
        # Find latest event strictly before decision
        prior_idx = int(np.searchsorted(series.timestamps_ns, decision_ns, side="left"))
        if prior_idx == 0:
            continue
        latest_event_ns = int(series.timestamps_ns[prior_idx - 1])
        if latest_event_ns < stale_cutoff_ns:
            continue  # Stale data guard triggered

        # Rate sum in lookback window
        rate_sum, count = interval_rate_sum(series, lookback_start_ns, decision_ns - 1)
        # Convert sum to daily rate
        rate_per_day = rate_sum / float(candidate.lookback_days)
        fresh_metrics[venue] = {
            "rate_per_day": rate_per_day,
            "rate_sum": rate_sum,
            "events": count,
            "latest_event_ns": latest_event_ns,
        }

    # Must have at least 2 fresh venues to establish a cross-venue pair
    if len(fresh_metrics) < 2:
        return None, {
            "reason": "INSUFFICIENT_FRESH_VENUES",
            "available_venues": len(fresh_metrics),
            "decision_time": decision_time.isoformat(),
        }

    # Sort venues by trailing funding rate
    ranked = sorted(fresh_metrics.items(), key=lambda item: (item[1]["rate_per_day"], item[0]))
    long_venue, long_meta = ranked[0]
    short_venue, short_meta = ranked[-1]

    # Forecast daily dispersion spread in basis points (bps)
    # Long pays lowest rate (or receives largest negative rate)
    # Short receives highest rate (or pays lowest negative rate)
    # Gross expected return = Short rate - Long rate
    forecast_spread_bps = (short_meta["rate_per_day"] - long_meta["rate_per_day"]) * 10_000.0

    audit = {
        "decision_time": decision_time.isoformat(),
        "long_venue": long_venue,
        "short_venue": short_venue,
        "long_rate_bps": long_meta["rate_per_day"] * 10_000.0,
        "short_rate_bps": short_meta["rate_per_day"] * 10_000.0,
        "forecast_spread_bps": forecast_spread_bps,
        "latest_signal_event_time": pd.Timestamp(
            max(long_meta["latest_event_ns"], short_meta["latest_event_ns"]), tz="UTC"
        ).isoformat(),
        "venues_compared": len(fresh_metrics),
    }

    if forecast_spread_bps < candidate.threshold_bps_per_day:
        audit["reason"] = "BELOW_THRESHOLD"
        return None, audit

    return PairTarget(
        long_venue=long_venue,
        short_venue=short_venue,
        forecast_bps_per_day=forecast_spread_bps,
    ), audit
