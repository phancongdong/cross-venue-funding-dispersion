# Cross-Venue Funding Rate Dispersion Strategy & Research

Independent quantitative research package and strategy engine for capturing delta-neutral funding rate dispersion across cryptocurrency perpetual swap venues (Bybit, OKX, Hyperliquid).

---

## 1. Directory Structure

```text
cross-venue-funding-dispersion/
│
├── README.md                                    # Project overview and execution guide
├── requirements.txt                             # Python dependencies (numpy, pandas, pyarrow, pytest)
├── run_backtest.py                              # Standalone CLI runner for backtesting
│
├── docs/                                        # Comprehensive research documentation
│   ├── CROSS_VENUE_FUNDING_DISPERSION_SYNTHESIS.md # Synthesis report of empirical findings
│   ├── CROSS_VENUE_FUNDING_DISPERSION_SPEC.md      # Frozen point-in-time specification
│   ├── CROSS_VENUE_FUNDING_DISPERSION_RESULTS.md   # Out-of-sample results by fold and symbol
│   ├── STRATEGY_GUIDE.md                           # Mathematical mechanics & capital requirements
│   └── DATA_SCHEMA.md                              # Multi-venue funding rate schema
│
├── src/                                         # Core strategy and execution engine
│   ├── __init__.py
│   ├── config.py                                # Venue, symbol, parameter, and cost configuration
│   ├── models.py                                # Domain models (VenueSeries, Candidate, PairTarget)
│   ├── data_loader.py                           # Parquet data loading & timestamp normalization
│   ├── signal_engine.py                         # Trailing rate estimation, ranking & signal generation
│   ├── simulator.py                             # Causal execution simulator with fee & funding accounting
│   ├── walk_forward.py                          # Multi-fold walk-forward evaluation engine
│   └── analytics.py                             # Performance metrics, drawdowns & bootstrap analysis
│
├── tests/                                       # Test suite for algorithm correctness
│   ├── __init__.py
│   └── test_funding_dispersion.py               # Unit tests verifying causality, guards & accounting
│
└── data/                                        # Historical funding rate datasets
    └── datasets/cross_venue_funding/
        ├── bybit/                               # Bybit USDT-M perpetual contracts
        ├── hyperliquid/                         # Hyperliquid native perpetual contracts
        └── okx/                                 # OKX USDT-M swap contracts
```

---

## 2. Environment Setup

Requirements: Python $\ge 3.10$.

```bash
pip install -r requirements.txt
```

---

## 3. Usage & Execution

### Run Backtest on a Single Asset (e.g., ETHUSDT)
```bash
# Standard transaction cost model (5 bps per leg):
python run_backtest.py --symbol ETHUSDT --lookback 14 --threshold 0

# Stress transaction cost model (10 bps per leg / 2x cost):
python run_backtest.py --symbol ETHUSDT --lookback 14 --threshold 0 --stress-cost
```

### Run Full Multi-Year Walk-Forward Optimization
```bash
python run_backtest.py --walk-forward
```

### Run Test Suite
```bash
pytest tests/test_funding_dispersion.py -v
```

---

## 4. Strategy & Algorithm Mechanics

1. **Daily Rebalance Cadence:** Decisions are computed daily at `00:00 UTC` and executed at `01:00 UTC` (1-hour execution delay to prevent lookahead bias).
2. **Trailing Lookback Window:** Historical funding rates are aggregated over rolling windows $L \in \{1, 3, 7, 14\}$ days for each available venue:
   $$\text{Rate}_{\text{daily}}(v) = \frac{\sum_{t \in [T - L, T)} \text{funding\_rate}(v, t)}{L}$$
3. **Delta-Neutral Venue Selection:**
   * **Long Leg:** Venue with the lowest (or most negative) trailing funding rate.
   * **Short Leg:** Venue with the highest trailing funding rate.
4. **Spread Threshold Guard:** Positions are only taken if the expected annualized spread satisfies:
   $$\text{Spread (bps/day)} = \left(\text{Rate}_{\text{daily}}(v_{\text{short}}) - \text{Rate}_{\text{daily}}(v_{\text{long}})\right) \times 10{,}000 \ge \text{Threshold}$$
5. **Staleness Guard (Fail-Closed):** If data from any participating venue is older than 12 hours, the engine automatically closes positions to cash (`STALE_EXIT`) to avoid unhedged directional exposure.
6. **Leg Turnover Accounting:** Transaction fees are accurately charged only on legs that transition (0, 1, or 2 actions per rebalance).

---

## 5. Empirical Findings & Research Conclusions

* **Gross Funding Yield:** Cross-venue funding dispersion generates positive gross funding cashflow across Bybit, OKX, and Hyperliquid ($+1,460,396\text{ VND}$ gross across selected walk-forward paths).
* **Cost Sensitivity:** High turnover destroys the edge under stress transaction costs ($10\text{ bps/leg}$), resulting in negative aggregate net PnL ($-17,617\text{ VND}$).
* **Capital Intensity:** The strategy requires significant capital buffers to absorb margin fragmentation across multiple exchanges, prevent liquidation from temporary basis divergence, and make thin daily basis-point yields economically viable after trading fees.
