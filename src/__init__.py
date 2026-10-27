"""Cross-Venue Funding Dispersion Strategy Package.

A quantitative strategy that captures delta-neutral cross-venue funding rate dispersion
between perpetual swap venues (e.g., Bybit, OKX, Hyperliquid).
"""

from .models import VenueSeries, Candidate, PairTarget, DispersionSignal
from .signal_engine import target_for_decision, interval_rate_sum, transition_actions
from .config import SYMBOL_VENUES, get_candidate_grid
from .data_loader import parse_funding_timestamps

__all__ = [
    "VenueSeries",
    "Candidate",
    "PairTarget",
    "DispersionSignal",
    "target_for_decision",
    "interval_rate_sum",
    "transition_actions",
    "SYMBOL_VENUES",
    "get_candidate_grid",
    "parse_funding_timestamps",
]

__version__ = "2.0.0"
