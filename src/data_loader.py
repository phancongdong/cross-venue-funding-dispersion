"""Data loading and verification module for cross-venue funding events."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .models import VenueSeries
from .config import DEFAULT_DATASET_DIR


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
        # Fallback for ISO strings with microsecond variations
        converted = [
            pd.Timestamp(v).tz_convert("UTC") if pd.Timestamp(v).tzinfo else pd.Timestamp(v, tz="UTC")
            for v in values
        ]
        parsed = pd.DatetimeIndex(converted)
    return parsed


def load_venue_series(
    symbol: str,
    venue: str,
    dataset_dir: Path | None = None
) -> VenueSeries:
    """Load and parse historical funding events for a symbol on a specific venue."""
    base_dir = dataset_dir or DEFAULT_DATASET_DIR
    path = base_dir / venue / f"{symbol}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")

    frame = pd.read_parquet(path)
    required = {
        "venue",
        "aitrade_symbol",
        "venue_symbol",
        "funding_time_ms",
        "funding_time_utc",
        "funding_rate",
        "source_channel",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path} missing required columns: {sorted(missing)}")

    if frame.empty:
        raise ValueError(f"{path} has zero rows")

    rates = pd.to_numeric(frame["funding_rate"], errors="coerce")
    if rates.isna().any():
        raise ValueError(f"{path} contains non-numeric funding rates")

    timestamps = parse_funding_timestamps(frame["funding_time_utc"])
    if timestamps.isna().any():
        raise ValueError(f"{path} contains invalid timestamps")

    # Sort strictly by timestamp
    ordered = pd.DataFrame({"ts": timestamps, "rate": rates.to_numpy(dtype=float)}).sort_values("ts")
    ts_array = ordered["ts"].to_numpy()
    if len(ts_array) > 1 and np.any(ts_array[1:] <= ts_array[:-1]):
        raise ValueError(f"{path} contains non-increasing or duplicate timestamps")

    parsed_series = pd.DatetimeIndex(ordered["ts"])
    ts_ns = np.asarray([ts.value for ts in parsed_series], dtype=np.int64)
    rate_array = ordered["rate"].to_numpy(dtype=float)

    return VenueSeries(
        symbol=symbol,
        venue=venue,
        path=path,
        timestamps_ns=ts_ns,
        rates=rate_array,
        prefix_rates=np.concatenate(([0.0], np.cumsum(rate_array))),
        rows=len(rate_array),
        first=parsed_series[0],
        last=parsed_series[-1],
        sha256=sha256_file(path),
    )


def load_all_venues_for_symbol(
    symbol: str,
    venues: Iterable[str],
    dataset_dir: Path | None = None
) -> dict[str, VenueSeries]:
    """Load all available venue series for a symbol."""
    series_map = {}
    for venue in venues:
        try:
            series_map[venue] = load_venue_series(symbol, venue, dataset_dir)
        except FileNotFoundError:
            continue
    return series_map
