#!/usr/bin/env python3
"""Example demonstration of Cross-Venue Funding Dispersion signal generation.

Shows how to feed live or historical venue funding rates into the signal engine
to identify delta-neutral arbitrage opportunities across perpetual swap exchanges.
"""

import pandas as pd
from src.data_loader import create_venue_series
from src.models import Candidate, PairTarget
from src.signal_engine import target_for_decision, transition_actions


def main():
    print("=" * 65)
    print("  Cross-Venue Funding Dispersion Strategy Demo")
    print("=" * 65)

    # 1. Sample trailing funding rates for BTCUSDT across Bybit, OKX, and Hyperliquid
    timestamps = [
        "2026-07-10T00:00:00Z",
        "2026-07-10T08:00:00Z",
        "2026-07-10T16:00:00Z",
        "2026-07-11T00:00:00Z",
        "2026-07-11T08:00:00Z",
        "2026-07-11T16:00:00Z",
        "2026-07-12T00:00:00Z",
    ]

    # Hyperliquid paying high funding (long pays short: positive rate)
    hl_rates = [0.00030, 0.00035, 0.00032, 0.00028, 0.00031, 0.00029, 0.00033]
    # Bybit paying low funding (negative or near-zero rate)
    bybit_rates = [-0.00005, -0.00002, 0.00000, -0.00003, -0.00001, -0.00004, -0.00002]
    # OKX paying moderate funding
    okx_rates = [0.00010, 0.00012, 0.00008, 0.00011, 0.00009, 0.00010, 0.00011]

    venues = {
        "hyperliquid": create_venue_series("BTCUSDT", "hyperliquid", timestamps, hl_rates),
        "bybit": create_venue_series("BTCUSDT", "bybit", timestamps, bybit_rates),
        "okx": create_venue_series("BTCUSDT", "okx", timestamps, okx_rates),
    }

    print(f"[+] Loaded venues: {list(venues.keys())}")

    # 2. Evaluate dispersion at decision timestamp
    decision_time = pd.Timestamp("2026-07-12T00:00:00Z")
    candidate = Candidate(lookback_days=1, threshold_bps_per_day=2.0)

    print(f"[+] Evaluating decision at {decision_time} with {candidate.candidate_id}...")
    target, audit = target_for_decision(venues, decision_time, candidate)

    if target is not None:
        print("\n[+] DELTA-NEUTRAL ARBITRAGE DETECTED:")
        print(f"    Long Venue         : {target.long_venue.upper()} (Lowest funding rate paid)")
        print(f"    Short Venue        : {target.short_venue.upper()} (Highest funding rate received)")
        print(f"    Forecast Spread    : {target.forecast_bps_per_day:.2f} bps/day")

        # Position transition calculation
        previous_target = PairTarget(long_venue="okx", short_venue="hyperliquid", forecast_bps_per_day=3.0)
        closed_legs, opened_legs = transition_actions(previous_target, target)
        print(f"    Rebalance Actions  : Close {closed_legs} leg(s), Open {opened_legs} leg(s)")
    else:
        print(f"\n[-] No target emitted: {audit.get('reason')}")

    print("\n" + "=" * 65)


if __name__ == "__main__":
    main()
