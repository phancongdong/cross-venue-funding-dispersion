"""Data loading and verification module for cross-venue funding events."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .models import VenueSeries


def sha256_file(path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_funding_timestamps(values: Iterable[Any]) -> pd.DatetimeIndex:
    """Parse funding timestamps accurately, handling mixed precision and timezone offsets."""
    parsed = pd.to_datetime(values, utc=True, errors="coerce")
    if parsed.isna().any():
        converted = [
            pd.Timestamp(v).tz_convert("UTC") if pd.Timestamp(v).tzinfo else pd.Timestamp(v, tz="UTC")
            for v in values
        ]
        parsed = pd.DatetimeIndex(converted)
    return parsed


def create_venue_series(
    symbol: str,
    venue: str,
    timestamps: Iterable[Any],
    rates: Iterable[float],
) -> VenueSeries:
    """Create a validated VenueSeries directly from in-memory arrays or API responses."""
    parsed = parse_funding_timestamps(timestamps)
    rate_arr = np.asarray(list(rates), dtype=float)

    if len(parsed) != len(rate_arr):
        raise ValueError("timestamps and rates must have identical length")
    if len(parsed) == 0:
        raise ValueError("Series cannot be empty")

    # Sort strictly by timestamp
    ordered = pd.DataFrame({"ts": parsed, "rate": rate_arr}).sort_values("ts")
    ts_array = ordered["ts"].to_numpy()
    if len(ts_array) > 1 and np.any(ts_array[1:] <= ts_array[:-1]):
        raise ValueError("contains non-increasing or duplicate timestamps")

    parsed_series = pd.DatetimeIndex(ordered["ts"])
    ts_ns = np.asarray([ts.value for ts in parsed_series], dtype=np.int64)
    rate_array = ordered["rate"].to_numpy(dtype=float)

    return VenueSeries(
        symbol=symbol,
        venue=venue,
        path=Path(f"{venue}_{symbol}"),
        timestamps_ns=ts_ns,
        rates=rate_array,
        prefix_rates=np.concatenate(([0.0], np.cumsum(rate_array))),
        rows=len(rate_array),
        first=parsed_series[0],
        last=parsed_series[-1],
        sha256="",
    )


def load_venue_series(
    symbol: str,
    venue: str,
    file_path: Path,
) -> VenueSeries:
    """Load and parse funding events for a symbol on a specific venue from parquet."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")

    frame = pd.read_parquet(path)
    if frame.empty:
        raise ValueError(f"{path} has zero rows")

    rates = pd.to_numeric(frame["funding_rate"], errors="coerce")
    if rates.isna().any():
        raise ValueError(f"{path} contains non-numeric funding rates")

    time_col = "funding_time_utc" if "funding_time_utc" in frame.columns else "timestamp"
    timestamps = parse_funding_timestamps(frame[time_col])

    return create_venue_series(symbol, venue, timestamps, rates)
