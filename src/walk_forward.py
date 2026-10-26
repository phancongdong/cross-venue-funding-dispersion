"""Point-in-Time Walk-Forward optimization and validation engine."""

from __future__ import annotations

from typing import Any
import pandas as pd

from .models import VenueSeries, Candidate, Fold
from .config import (
    get_candidate_grid,
    NORMAL_ONE_WAY_LEG_COST,
    STRESS_ONE_WAY_LEG_COST,
    DEFAULT_FOLDS,
    INITIAL_EQUITY_VND,
    DATA_CUTOFF,
)
from .simulator import build_strategy_path, slice_strategy_path, replay_strategy_path


def select_best_candidate_for_train(
    symbol: str,
    venues: dict[str, VenueSeries],
    train_end: pd.Timestamp,
    candidates: list[Candidate] | None = None,
    min_active_days: int = 90,
    min_episodes: int = 12,
) -> tuple[Candidate | None, list[dict[str, Any]]]:
    """Evaluate candidate grid on in-sample data strictly up to train_end.

    Selection rules:
    - Candidate must have at least `min_active_days` and `min_episodes`.
    - Candidate must have positive return under stress 2x costs.
    - Among qualifying candidates, rank by highest normal return.
    """
    candidates = candidates or get_candidate_grid()
    evaluations: list[dict[str, Any]] = []

    # First timestamp across available venues
    first_ts = min(v.first for v in venues.values())
    if first_ts >= train_end:
        return None, []

    for candidate in candidates:
        try:
            full_path = build_strategy_path(symbol, venues, candidate, first_ts, train_end)
            normal_sim = replay_strategy_path(full_path, NORMAL_ONE_WAY_LEG_COST)
            stress_sim = replay_strategy_path(full_path, STRESS_ONE_WAY_LEG_COST)
        except Exception:
            continue

        norm_m = normal_sim["metrics"]
        stress_m = stress_sim["metrics"]

        record = {
            "symbol": symbol,
            "candidate_id": candidate.candidate_id,
            "lookback_days": candidate.lookback_days,
            "threshold_bps": candidate.threshold_bps_per_day,
            "normal_pnl_vnd": norm_m["pnl_vnd"],
            "normal_return_pct": norm_m["return_pct"],
            "normal_pf": norm_m["profit_factor"],
            "stress_pnl_vnd": stress_m["pnl_vnd"],
            "stress_return_pct": stress_m["return_pct"],
            "stress_pf": stress_m["profit_factor"],
            "active_days": norm_m["active_days"],
            "episodes": norm_m["episodes"],
            "eligible": (
                norm_m["active_days"] >= min_active_days
                and norm_m["episodes"] >= min_episodes
                and stress_m["return_pct"] > 0.0
            ),
        }
        evaluations.append(record)

    eligible = [e for e in evaluations if e["eligible"]]
    if not eligible:
        return None, evaluations

    # Pick candidate with highest normal return
    best_record = max(eligible, key=lambda x: (x["normal_return_pct"], x["stress_return_pct"]))
    best_cand = Candidate(
        lookback_days=best_record["lookback_days"],
        threshold_bps_per_day=best_record["threshold_bps"],
    )
    return best_cand, evaluations


def run_symbol_walk_forward(
    symbol: str,
    venues: dict[str, VenueSeries],
    folds: list[Fold] | tuple[Fold, ...] = DEFAULT_FOLDS,
) -> list[dict[str, Any]]:
    """Execute point-in-time walk forward for a symbol across folds."""
    results = []

    for fold in folds:
        first_ts = min(v.first for v in venues.values())
        if first_ts >= fold.oos_end:
            continue

        best_cand, train_grid = select_best_candidate_for_train(
            symbol, venues, fold.train_end
        )

        if best_cand is None:
            # Fall back to cash
            results.append(
                {
                    "symbol": symbol,
                    "fold": fold.name,
                    "selected_candidate_id": "CASH",
                    "normal_active_days": 0,
                    "normal_pnl_vnd": 0.0,
                    "normal_return_pct": 0.0,
                    "stress_pnl_vnd": 0.0,
                    "stress_return_pct": 0.0,
                    "status": "NO_ELIGIBLE_TRAIN_CANDIDATE",
                }
            )
            continue

        # Run OOS
        full_oos_path = build_strategy_path(symbol, venues, best_cand, first_ts, fold.oos_end)
        # Replay only the OOS portion
        normal_sim = replay_strategy_path(full_oos_path, NORMAL_ONE_WAY_LEG_COST)
        stress_sim = replay_strategy_path(full_oos_path, STRESS_ONE_WAY_LEG_COST)

        # Filter daily rows to OOS window
        oos_start_str = str(fold.oos_start.date())
        oos_daily_norm = [r for r in normal_sim["daily_rows"] if r["date"] >= oos_start_str]
        oos_daily_stress = [r for r in stress_sim["daily_rows"] if r["date"] >= oos_start_str]

        oos_norm_pnl = sum(r["pnl_vnd"] for r in oos_daily_norm)
        oos_stress_pnl = sum(r["pnl_vnd"] for r in oos_daily_stress)
        active_days = sum(1 for r in oos_daily_norm if r["active_hours"] > 0)

        results.append(
            {
                "symbol": symbol,
                "fold": fold.name,
                "selected_candidate_id": best_cand.candidate_id,
                "lookback_days": best_cand.lookback_days,
                "threshold_bps": best_cand.threshold_bps_per_day,
                "normal_active_days": active_days,
                "normal_pnl_vnd": oos_norm_pnl,
                "normal_return_pct": 100.0 * (oos_norm_pnl / INITIAL_EQUITY_VND),
                "stress_pnl_vnd": oos_stress_pnl,
                "stress_return_pct": 100.0 * (oos_stress_pnl / INITIAL_EQUITY_VND),
                "status": "COMPLETED",
            }
        )

    return results
