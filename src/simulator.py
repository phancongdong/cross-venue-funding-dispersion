"""Execution simulator and cost accounting for cross-venue funding dispersion."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .models import VenueSeries, Candidate, PairTarget
from .signal_engine import target_for_decision, interval_rate_sum
from .config import INITIAL_EQUITY_VND, STALE_HOURS


def target_is_stale(
    venues: dict[str, VenueSeries],
    target: PairTarget,
    current_time: pd.Timestamp,
    stale_hours: float = STALE_HOURS,
) -> bool:
    """Check if any venue in the active target has become stale."""
    cutoff_ns = int((current_time - pd.Timedelta(hours=stale_hours)).value)
    curr_ns = int(current_time.value)
    for venue_name in (target.long_venue, target.short_venue):
        series = venues[venue_name]
        idx = int(np.searchsorted(series.timestamps_ns, curr_ns, side="left"))
        if idx == 0:
            return True
        latest_ns = int(series.timestamps_ns[idx - 1])
        if latest_ns < cutoff_ns:
            return True
    return False


def transition_actions(
    current: PairTarget | None, next_target: PairTarget | None
) -> tuple[int, int]:
    """Calculate the number of closed and opened legs between consecutive targets.

    Returns:
        (closed_legs, opened_legs)
    """
    old_legs = (
        {(current.long_venue, 1), (current.short_venue, -1)}
        if current is not None
        else set()
    )
    new_legs = (
        {(next_target.long_venue, 1), (next_target.short_venue, -1)}
        if next_target is not None
        else set()
    )
    return len(old_legs - new_legs), len(new_legs - old_legs)


def build_strategy_path(
    symbol: str,
    venues: dict[str, VenueSeries],
    candidate: Candidate,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, Any]:
    """Build the cost-independent causal execution and funding event path."""
    if start >= end:
        raise ValueError("start must be earlier than end")
    start = start.ceil("h")
    end = end.floor("h")

    current: PairTarget | None = None
    queued: tuple[pd.Timestamp, PairTarget | None, str] | None = None
    events: list[dict[str, Any]] = []
    active_hours: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    decision_rows: list[dict[str, Any]] = []
    stale_exit_count = 0
    latest_signal_event: pd.Timestamp | None = None
    latest_realized_event: pd.Timestamp | None = None

    def execute_target(
        timestamp: pd.Timestamp, target: PairTarget | None, reason: str
    ) -> None:
        nonlocal current
        curr_id = (current.long_venue, current.short_venue) if current else None
        target_id = (target.long_venue, target.short_venue) if target else None
        if curr_id == target_id:
            return
        events.append(
            {
                "kind": "transition",
                "timestamp": timestamp,
                "target": target,
                "reason": reason,
            }
        )
        current = target

    def append_funding(
        interval_start: pd.Timestamp,
        interval_end: pd.Timestamp,
        exact_only: bool = False,
    ) -> None:
        nonlocal latest_realized_event
        if current is None:
            return
        long_series = venues[current.long_venue]
        short_series = venues[current.short_venue]

        if exact_only:
            long_rate, l_cnt = interval_rate_sum(long_series, int(interval_start.value), int(interval_start.value))
            short_rate, s_cnt = interval_rate_sum(short_series, int(interval_start.value), int(interval_start.value))
            event_count = l_cnt + s_cnt
        else:
            long_rate, l_cnt = interval_rate_sum(
                long_series, int(interval_start.value) + 1, int(interval_end.value)
            )
            short_rate, s_cnt = interval_rate_sum(
                short_series, int(interval_start.value) + 1, int(interval_end.value)
            )
            event_count = l_cnt + s_cnt

        net_rate = short_rate - long_rate

        interval_latest: pd.Timestamp | None = None
        for v in (current.long_venue, current.short_venue):
            s = venues[v]
            if exact_only:
                left = int(np.searchsorted(s.timestamps_ns, interval_start.value, side="left"))
                right = int(np.searchsorted(s.timestamps_ns, interval_start.value, side="right"))
            else:
                left = int(np.searchsorted(s.timestamps_ns, interval_start.value, side="right"))
                right = int(np.searchsorted(s.timestamps_ns, interval_end.value, side="left"))
            if right > left:
                ev_time = pd.Timestamp(int(s.timestamps_ns[right - 1]), tz="UTC")
                interval_latest = ev_time if interval_latest is None else max(interval_latest, ev_time)
                latest_realized_event = (
                    ev_time if latest_realized_event is None else max(latest_realized_event, ev_time)
                )

        if event_count or net_rate:
            events.append(
                {
                    "kind": "funding",
                    "timestamp": interval_start,
                    "net_rate": net_rate,
                    "event_count": event_count,
                    "latest_event_time": interval_latest,
                }
            )

    _NO_DECISION = object()
    for hour in pd.date_range(start=start, end=end, freq="1h", inclusive="left"):
        hour = pd.Timestamp(hour)
        next_hour = min(hour + pd.Timedelta(hours=1), end)

        append_funding(hour, hour, exact_only=True)
        if queued is not None and queued[0] == hour:
            execute_target(hour, queued[1], queued[2])
            queued = None
        append_funding(hour, next_hour)

        if current is not None:
            active_hours[str(hour.date())] += 1

        desired: PairTarget | None | object = _NO_DECISION
        reason = ""
        if hour.hour == 0:
            desired, audit = target_for_decision(venues, hour, candidate)
            decision_counts[audit.get("reason", "OK")] += 1
            decision_rows.append(audit)
            if audit.get("latest_signal_event_time"):
                signal_time = pd.Timestamp(audit["latest_signal_event_time"])
                latest_signal_event = (
                    signal_time
                    if latest_signal_event is None
                    else max(latest_signal_event, signal_time)
                )
            reason = "DAILY_REBALANCE" if desired is not None else "DAILY_CASH"
        elif current is not None and target_is_stale(venues, current, hour):
            desired = None
            reason = "STALE_EXIT"
            stale_exit_count += 1

        execution_time = hour + pd.Timedelta(hours=1)
        if desired is not _NO_DECISION and execution_time < end:
            queued = (execution_time, desired, reason)

    if current is not None:
        execute_target(end - pd.Timedelta(nanoseconds=1), None, "BOUNDARY_CLOSE")

    return {
        "symbol": symbol,
        "candidate": candidate,
        "start": start,
        "end": end,
        "events": events,
        "active_hours": dict(active_hours),
        "decision_rows": decision_rows,
        "decision_status_counts": dict(sorted(decision_counts.items())),
        "stale_exits": stale_exit_count,
        "latest_signal_event_time": (
            latest_signal_event.isoformat() if latest_signal_event is not None else None
        ),
        "latest_realized_event_time": (
            latest_realized_event.isoformat() if latest_realized_event is not None else None
        ),
    }


def slice_strategy_path(strategy_path: dict[str, Any], end: pd.Timestamp) -> dict[str, Any]:
    """Slice an existing strategy path up to a prior boundary timestamp."""
    start = pd.Timestamp(strategy_path["start"])
    end = pd.Timestamp(end).floor("h")
    if not start < end <= pd.Timestamp(strategy_path["end"]):
        raise ValueError("slice end must be inside the strategy path")

    events = [
        event for event in strategy_path["events"] if pd.Timestamp(event["timestamp"]) < end
    ]
    current: PairTarget | None = None
    for event in events:
        if event["kind"] == "transition":
            current = event["target"]
    if current is not None:
        events.append(
            {
                "kind": "transition",
                "timestamp": end - pd.Timedelta(nanoseconds=1),
                "target": None,
                "reason": "BOUNDARY_CLOSE",
            }
        )

    decisions = [
        row for row in strategy_path["decision_rows"] if pd.Timestamp(row["decision_time"]) < end
    ]
    decision_counts = Counter(row.get("reason", "OK") for row in decisions)
    signal_times = [
        pd.Timestamp(row["latest_signal_event_time"])
        for row in decisions
        if row.get("latest_signal_event_time")
    ]
    realized_times = [
        pd.Timestamp(event["latest_event_time"])
        for event in events
        if event["kind"] == "funding" and event.get("latest_event_time") is not None
    ]
    active_hours = {
        date: hours
        for date, hours in strategy_path["active_hours"].items()
        if pd.Timestamp(date, tz="UTC") < end
    }
    stale_exits = sum(
        event["kind"] == "transition" and event["reason"] == "STALE_EXIT" for event in events
    )
    return {
        **strategy_path,
        "end": end,
        "events": events,
        "active_hours": active_hours,
        "decision_rows": decisions,
        "decision_status_counts": dict(sorted(decision_counts.items())),
        "stale_exits": stale_exits,
        "latest_signal_event_time": (
            max(signal_times).isoformat() if signal_times else None
        ),
        "latest_realized_event_time": (
            max(realized_times).isoformat() if realized_times else None
        ),
    }


def replay_strategy_path(
    strategy_path: dict[str, Any],
    one_way_leg_cost: float,
    initial_equity: float = INITIAL_EQUITY_VND,
) -> dict[str, Any]:
    """Replay an execution path under a specific transaction cost model."""
    symbol = str(strategy_path["symbol"])
    candidate = strategy_path["candidate"]
    start = pd.Timestamp(strategy_path["start"])
    end = pd.Timestamp(strategy_path["end"])

    equity = initial_equity
    current: PairTarget | None = None
    current_episode: dict[str, Any] | None = None
    episodes: list[dict[str, Any]] = []

    daily: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "pnl_vnd": 0.0,
            "funding_pnl_vnd": 0.0,
            "fees_vnd": 0.0,
            "active_hours": 0,
            "funding_events": 0,
        }
    )
    for date, hours in strategy_path["active_hours"].items():
        daily[date]["active_hours"] = int(hours)
    turnover_actions = 0

    def book_fee(timestamp: pd.Timestamp, actions: int) -> float:
        nonlocal equity, turnover_actions
        if actions <= 0:
            return 0.0
        fee = equity * one_way_leg_cost * actions
        equity -= fee
        turnover_actions += actions
        row = daily[str(timestamp.date())]
        row["pnl_vnd"] -= fee
        row["fees_vnd"] += fee
        return fee

    def close_episode(timestamp: pd.Timestamp, fee: float, reason: str) -> None:
        nonlocal current_episode
        if current_episode is None:
            return
        current_episode["fees_vnd"] += fee
        current_episode["pnl_vnd"] = (
            current_episode["funding_pnl_vnd"] - current_episode["fees_vnd"]
        )
        current_episode["end_time"] = timestamp.isoformat()
        current_episode["exit_reason"] = reason
        episodes.append(current_episode)
        current_episode = None

    for event in strategy_path["events"]:
        timestamp = pd.Timestamp(event["timestamp"])
        if event["kind"] == "funding":
            if current is None or current_episode is None:
                raise RuntimeError("Funding event without an active pair")
            pnl = equity * float(event["net_rate"])
            equity += pnl
            row = daily[str(timestamp.date())]
            row["pnl_vnd"] += pnl
            row["funding_pnl_vnd"] += pnl
            row["funding_events"] += int(event["event_count"])
            current_episode["funding_pnl_vnd"] += pnl

        elif event["kind"] == "transition":
            next_target: PairTarget | None = event["target"]
            closed_legs, opened_legs = transition_actions(current, next_target)
            close_fee = book_fee(timestamp, closed_legs)
            close_episode(timestamp, close_fee, str(event["reason"]))
            open_fee = book_fee(timestamp, opened_legs)
            if next_target is not None:
                current_episode = {
                    "symbol": symbol,
                    "long_venue": next_target.long_venue,
                    "short_venue": next_target.short_venue,
                    "start_time": timestamp.isoformat(),
                    "end_time": None,
                    "forecast_bps_per_day": float(next_target.forecast_bps_per_day),
                    "entry_reason": str(event["reason"]),
                    "exit_reason": None,
                    "funding_pnl_vnd": 0.0,
                    "fees_vnd": open_fee,
                    "pnl_vnd": -open_fee,
                }
            current = next_target

    daily_rows: list[dict[str, Any]] = []
    cumulative_pnl = 0.0
    for day in pd.date_range(start.floor("D"), end.ceil("D"), freq="D"):
        date_str = str(day.date())
        row = daily[date_str]
        pnl = row["pnl_vnd"]
        cumulative_pnl += pnl
        daily_rows.append(
            {
                "date": date_str,
                "pnl_vnd": pnl,
                "cumulative_pnl_vnd": cumulative_pnl,
                "funding_pnl_vnd": row["funding_pnl_vnd"],
                "fees_vnd": row["fees_vnd"],
                "active_hours": row["active_hours"],
                "funding_events": row["funding_events"],
            }
        )

    # Compute key metrics
    total_pnl = equity - initial_equity
    return_pct = 100.0 * (total_pnl / initial_equity)
    daily_pnls = [r["pnl_vnd"] for r in daily_rows]
    gains = sum(p for p in daily_pnls if p > 0.0)
    losses = -sum(p for p in daily_pnls if p < 0.0)
    pf = gains / losses if losses > 0.0 else (99.0 if gains > 0.0 else 0.0)

    # Peak-to-trough max drawdown
    peak = initial_equity
    running_eq = initial_equity
    max_dd = 0.0
    for p in daily_pnls:
        running_eq += p
        peak = max(peak, running_eq)
        if peak > 0.0:
            max_dd = max(max_dd, 100.0 * (peak - running_eq) / peak)

    active_days = sum(1 for r in daily_rows if r["active_hours"] > 0)

    metrics = {
        "symbol": symbol,
        "candidate_id": candidate.candidate_id,
        "one_way_leg_cost": one_way_leg_cost,
        "initial_equity_vnd": initial_equity,
        "ending_equity_vnd": equity,
        "pnl_vnd": total_pnl,
        "return_pct": return_pct,
        "profit_factor": pf,
        "max_drawdown_pct": max_dd,
        "gross_funding_pnl_vnd": sum(r["funding_pnl_vnd"] for r in daily_rows),
        "fees_vnd": sum(r["fees_vnd"] for r in daily_rows),
        "turnover_actions": turnover_actions,
        "active_days": active_days,
        "active_hours": sum(r["active_hours"] for r in daily_rows),
        "episodes": len(episodes),
        "stale_exits": strategy_path["stale_exits"],
        "latest_signal_event_time": strategy_path["latest_signal_event_time"],
        "latest_realized_event_time": strategy_path["latest_realized_event_time"],
    }

    return {
        "metrics": metrics,
        "daily_rows": daily_rows,
        "episodes": episodes,
        "strategy_path": strategy_path,
    }


def simulate_candidate(
    symbol: str,
    venues: dict[str, VenueSeries],
    candidate: Candidate,
    start: pd.Timestamp,
    end: pd.Timestamp,
    one_way_leg_cost: float,
    strategy_path: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convenience runner: build strategy path (if not provided) and replay under given cost."""
    if strategy_path is None:
        strategy_path = build_strategy_path(symbol, venues, candidate, start, end)
    return replay_strategy_path(strategy_path, one_way_leg_cost)
