"""Standalone CLI Runner for Cross-Venue Funding Dispersion Strategy.

Usage:
    python run_backtest.py --symbol ETHUSDT --lookback 14 --threshold 0
    python run_backtest.py --walk-forward
    python run_backtest.py --all-symbols
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import pandas as pd

from src.config import (
    SYMBOL_VENUES,
    DEFAULT_DATASET_DIR,
    NORMAL_ONE_WAY_LEG_COST,
    STRESS_ONE_WAY_LEG_COST,
    DEFAULT_FOLDS,
    DATA_CUTOFF,
)
from src.models import Candidate
from src.data_loader import load_all_venues_for_symbol
from src.simulator import build_strategy_path, replay_strategy_path
from src.walk_forward import run_symbol_walk_forward
from src.analytics import aggregate_portfolio_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Cross-Venue Funding Dispersion Backtest"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="ETHUSDT",
        choices=list(SYMBOL_VENUES.keys()),
        help="Target crypto perpetual symbol",
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=14,
        choices=[1, 3, 7, 14],
        help="Lookback window in days for trailing funding calculation",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        choices=[0.0, 2.0, 5.0],
        help="Minimum spread threshold in bps/day",
    )
    parser.add_argument(
        "--stress-cost",
        action="store_true",
        help="Use 2x stress transaction cost (10 bps/leg instead of 5 bps)",
    )
    parser.add_argument(
        "--walk-forward",
        action="store_true",
        help="Execute full multi-year walk-forward optimization across all symbols",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATASET_DIR,
        help="Custom path to dataset directory",
    )
    return parser.parse_args()


def run_single_symbol(
    symbol: str,
    candidate: Candidate,
    cost: float,
    data_dir: Path,
    cost_label: str = "Normal",
) -> None:
    venues_to_load = SYMBOL_VENUES[symbol]
    series_map = load_all_venues_for_symbol(symbol, venues_to_load, data_dir)
    if len(series_map) < 2:
        print(f"[-] Insufficient venues available for {symbol}: found {list(series_map.keys())}")
        return

    first_ts = min(v.first for v in series_map.values())
    print(f"\n{'='*70}")
    print(f"CROSS-VENUE FUNDING DISPERSION: {symbol}")
    print(f"Venues: {sorted(series_map.keys())}")
    print(f"Candidate: Lookback={candidate.lookback_days}d, Threshold={candidate.threshold_bps_per_day} bps/day")
    print(f"Cost Model: {cost_label} ({cost*10000:.1f} bps per side)")
    print(f"Data Span: {first_ts.date()} -> {DATA_CUTOFF.date()}")
    print(f"{'='*70}")

    path = build_strategy_path(symbol, series_map, candidate, first_ts, DATA_CUTOFF)
    sim = replay_strategy_path(path, cost)
    m = sim["metrics"]

    print("\n--- PERFORMANCE SUMMARY ---")
    print(f"Initial Capital    : {m['initial_equity_vnd']:,.0f} VND")
    print(f"Ending Capital     : {m['ending_equity_vnd']:,.0f} VND")
    print(f"Net PnL            : {m['pnl_vnd']:+,.0f} VND ({m['return_pct']:+.2f}%)")
    print(f"Gross Funding PnL  : {m['gross_funding_pnl_vnd']:+,.0f} VND")
    print(f"Transaction Fees   : {m['fees_vnd']:,.0f} VND")
    print(f"Profit Factor      : {m['profit_factor']:.2f}")
    print(f"Max Drawdown       : {m['max_drawdown_pct']:.2f}%")
    print(f"Active Trading Days: {m['active_days']} days ({m['active_hours']} hours)")
    print(f"Total Episodes     : {m['episodes']}")
    print(f"Turnover Actions   : {m['turnover_actions']} leg fills")
    print(f"Stale Guard Exits  : {m['stale_exits']}")


def run_full_walk_forward(data_dir: Path) -> None:
    print(f"\n{'='*80}")
    print("EXECUTING CROSS-VENUE FUNDING DISPERSION WALK-FORWARD STUDY (Y2024 - Y2026)")
    print(f"{'='*80}\n")

    all_results = []
    for symbol, venues in SYMBOL_VENUES.items():
        print(f"[*] Processing {symbol} ({len(venues)} venues)...", end="", flush=True)
        series_map = load_all_venues_for_symbol(symbol, venues, data_dir)
        if len(series_map) < 2:
            print(" SKIPPED (insufficient venues)")
            continue

        sym_res = run_symbol_walk_forward(symbol, series_map, DEFAULT_FOLDS)
        all_results.extend(sym_res)
        print(" DONE")

    # Format into DataFrame
    df = pd.DataFrame(all_results)
    print("\n" + df.to_string(index=False))

    agg = aggregate_portfolio_results(all_results)
    print(f"\n{'='*80}")
    print("PORTFOLIO AGGREGATE WALK-FORWARD SUMMARY")
    print(f"{'='*80}")
    print(f"Total Active Routes : {agg['total_active_routes']}")
    print(f"Normal Net PnL      : {agg['normal_pnl_vnd']:+,.0f} VND (Mean: {agg['normal_mean_return_pct']:+.2f}%)")
    print(f"Stress 2x Net PnL   : {agg['stress_2x_pnl_vnd']:+,.0f} VND (Mean: {agg['stress_2x_mean_return_pct']:+.2f}%)")
    print(f"Stress Edge Retained: {agg['stress_edge_retention']*100:.2f}%")
    print(f"Positive Stress Wins: {agg['positive_stress_routes']}/{agg['sufficient_sample_routes']} ({agg['breadth_ratio']*100:.1f}%)")
    print(f"Max Concentration   : {agg['max_positive_symbol_concentration']*100:.1f}%")
    print(f"Bootstrap P(Mean>0) : {agg['bootstrap_stress_return']['probability_mean_positive']*100:.1f}%")
    print(f"{'='*80}\n")


def main() -> None:
    args = parse_args()
    if args.walk_forward:
        run_full_walk_forward(args.data_dir)
    else:
        candidate = Candidate(args.lookback, args.threshold)
        cost = STRESS_ONE_WAY_LEG_COST if args.stress_cost else NORMAL_ONE_WAY_LEG_COST
        label = "Stress (2x)" if args.stress_cost else "Normal (1x)"
        run_single_symbol(args.symbol, candidate, cost, args.data_dir, label)


if __name__ == "__main__":
    main()
