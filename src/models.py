"""Data models and structures for cross-venue funding dispersion strategy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class VenueSeries:
    """Historical funding rate series for a specific symbol on a specific venue."""

    symbol: str
    venue: str
    path: Path
    timestamps_ns: np.ndarray  # int64 Unix nanoseconds
    rates: np.ndarray          # float64 funding rates
    prefix_rates: np.ndarray   # float64 cumulative sum for O(1) interval rate sum
    rows: int
    first: pd.Timestamp
    last: pd.Timestamp
    sha256: str


@dataclass(frozen=True)
class Candidate:
    """Strategy candidate parameter tuple."""

    lookback_days: int
    threshold_bps_per_day: float

    @property
    def candidate_id(self) -> str:
        return f"FUNDING_DISPERSION|L{self.lookback_days}D|T{self.threshold_bps_per_day:.0f}BPS"


@dataclass(frozen=True)
class PairTarget:
    """Target position at a decision time."""

    long_venue: str
    short_venue: str
    forecast_bps_per_day: float


@dataclass(frozen=True)
class Fold:
    """Walk-forward train and out-of-sample window definition."""

    name: str
    train_end: pd.Timestamp
    oos_start: pd.Timestamp
    oos_end: pd.Timestamp


@dataclass
class Episode:
    """Continuous period during which a specific pair of venues is held."""

    symbol: str
    long_venue: str
    short_venue: str
    start_time: pd.Timestamp
    end_time: pd.Timestamp
    duration_hours: float
    gross_funding_pnl: float
    fees: float
    net_pnl: float
