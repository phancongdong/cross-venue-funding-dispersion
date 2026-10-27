"""Configuration parameters for Cross-Venue Funding Dispersion strategy."""

from pathlib import Path
from .models import Candidate

# Base directories
PACKAGE_ROOT = Path(__file__).resolve().parents[1]

# Universe definition: Symbols and their available perpetual venues
SYMBOL_VENUES = {
    "BTCUSDT": ("bybit", "hyperliquid", "okx"),
    "DOGEUSDT": ("bybit", "hyperliquid", "okx"),
    "ETHUSDT": ("bybit", "hyperliquid", "okx"),
    "IOTAUSDT": ("bybit", "hyperliquid", "okx"),
    "MEWUSDT": ("bybit", "hyperliquid", "okx"),
    "PEPEUSDT": ("hyperliquid", "okx"),
    "TAOUSDT": ("bybit", "hyperliquid", "okx"),
    "THETAUSDT": ("bybit", "okx"),
    "WLDUSDT": ("bybit", "hyperliquid", "okx"),
    "YFIUSDT": ("bybit", "okx"),
    "ZECUSDT": ("bybit", "hyperliquid", "okx"),
}

# Execution & operational assumptions
NORMAL_ONE_WAY_LEG_COST = 0.0005   # 5 bps per side (0.05%)
STRESS_ONE_WAY_LEG_COST = 0.0010   # 10 bps per side (stress test: 2x normal)
STALE_HOURS = 12.0                 # Stale data guard threshold (fail-closed)
EXECUTION_DELAY_HOURS = 1.0        # Delay from decision time (00:00 UTC) to fill (01:00 UTC)

# Parameter grid
LOOKBACK_DAYS = [1, 3, 7, 14]
THRESHOLD_BPS_PER_DAY = [0.0, 2.0, 5.0]


def get_candidate_grid() -> list[Candidate]:
    """Generate the full parameter candidate grid."""
    return [
        Candidate(lookback_days=lb, threshold_bps_per_day=th)
        for lb in LOOKBACK_DAYS
        for th in THRESHOLD_BPS_PER_DAY
    ]
