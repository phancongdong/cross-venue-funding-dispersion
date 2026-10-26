"""Analytics, performance metrics, and bootstrap confidence intervals."""

from __future__ import annotations

from typing import Iterable, Any
from collections import defaultdict

import numpy as np


def bootstrap_probability_positive(
    returns: Iterable[float],
    samples: int = 10_000,
    seed: int = 20260802
) -> dict[str, Any]:
    """Compute bootstrap distribution of the mean return over independent samples."""
    values = np.asarray(list(returns), dtype=float)
    if len(values) == 0:
        return {
            "samples": samples,
            "observations": 0,
            "probability_mean_positive": 0.0,
            "median_mean_pct": 0.0,
            "lower_95_pct": 0.0,
            "upper_95_pct": 0.0,
        }

    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(samples, len(values)))
    means = np.mean(values[indices], axis=1)

    return {
        "samples": samples,
        "observations": len(values),
        "probability_mean_positive": float(np.mean(means > 0.0)),
        "median_mean_pct": float(np.median(means)),
        "lower_95_pct": float(np.quantile(means, 0.025)),
        "upper_95_pct": float(np.quantile(means, 0.975)),
    }


def aggregate_portfolio_results(fold_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate multiple symbol/fold walk-forward results."""
    active_rows = [r for r in fold_results if r.get("selected_candidate_id") != "CASH"]
    normal_pnl = sum(r["normal_pnl_vnd"] for r in active_rows)
    stress_pnl = sum(r["stress_pnl_vnd"] for r in active_rows)
    retention = (stress_pnl / normal_pnl) if normal_pnl > 0.0 else 0.0

    # Breadth
    sufficient = [r for r in active_rows if r.get("normal_active_days", 0) >= 30]
    positive_stress = sum(1 for r in sufficient if r["stress_pnl_vnd"] > 0.0)
    breadth = positive_stress / len(sufficient) if sufficient else 0.0

    # Concentration
    contribution: dict[str, float] = defaultdict(float)
    for r in active_rows:
        if r["normal_pnl_vnd"] > 0.0:
            contribution[r["symbol"]] += r["normal_pnl_vnd"]
    total_pos = sum(contribution.values())
    max_concentration = max(contribution.values()) / total_pos if total_pos > 0.0 else 0.0

    stress_returns = [r["stress_return_pct"] for r in active_rows]
    bootstrap = bootstrap_probability_positive(stress_returns)

    return {
        "total_active_routes": len(active_rows),
        "sufficient_sample_routes": len(sufficient),
        "normal_pnl_vnd": normal_pnl,
        "stress_2x_pnl_vnd": stress_pnl,
        "normal_mean_return_pct": float(np.mean([r["normal_return_pct"] for r in active_rows])) if active_rows else 0.0,
        "stress_2x_mean_return_pct": float(np.mean(stress_returns)) if stress_returns else 0.0,
        "stress_edge_retention": retention,
        "positive_stress_routes": positive_stress,
        "breadth_ratio": breadth,
        "max_positive_symbol_concentration": max_concentration,
        "bootstrap_stress_return": bootstrap,
    }
