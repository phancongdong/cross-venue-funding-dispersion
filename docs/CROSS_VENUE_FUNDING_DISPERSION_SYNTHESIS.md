# Cross-Venue Funding Dispersion Research Synthesis

Date: 2026-08-02 (Asia/Saigon)

Scope: `LOCAL/RESEARCH/HISTORICAL_POST_SELECTED`.

Live authority: `NONE`. Deployment permitted: `false`.

---

## 1. Executive Summary

The strategy of buying perpetual contracts on the venue with the lowest funding rate and selling the same instrument on the venue with the highest funding rate fails the frozen verification criteria. Final verdict:

`FUNDING_DISPERSION_REJECTED_HISTORICAL`

While funding rate dispersion exists historically and generates positive gross funding cashflow, it is not stable across market regimes and is excessively sensitive to turnover transaction costs. Furthermore, this is a funding-only backtest: it omits synchronized basis PnL, mark-price divergence, order-book depth, execution latency, margin fragmentation, and liquidation risk. Therefore, even positive normal-cost returns cannot support live deployment.

---

## 2. Frozen Methodology

- **Universe:** 11 crypto perpetual symbols with at least two verified venues across OKX, Bybit, and Hyperliquid.
- **Event-Level Data:** 30 Parquet files verified by SHA-256 / CRC.
- **Decision Schedule:** Daily decisions at `00:00 UTC`; execution simulated with a 1-hour delay.
- **Sizing:** 1x equity long on lowest trailing-funding venue, 1x equity short on highest venue; total gross leverage 2x (below 3x cap).
- **Staleness Guard:** Hourly fail-closed when funding feed is older than 12 hours.
- **Candidate Grid:** 12 candidates: Lookback `[1, 3, 7, 14]` days $\times$ Threshold `[0, 2, 5]` bps/day.
- **Walk-Forward Design:** Expanding in-sample train with locked out-of-sample (OOS) folds: Y2024, Y2025, Y2026 partial.
- **Transaction Costs:** Normal 5 bps per one-way leg action; exact stress 2x at 10 bps.
- **Account Model:** 1,000,000 VND standalone account per symbol/fold; no cross-portfolio pooling.

---

## 3. Aggregate Out-Of-Sample Results

| Metric | Result |
|---|---:|
| Train-grid rows evaluated | 396 |
| Fold selections | 33 |
| Selected symbol/folds | 25 |
| Routes with $\ge$ 30 active OOS days | 20 |
| Normal Cost Net PnL | +719,251 VND |
| Stress Cost 2x Net PnL | -17,617 VND |
| Positive Stress Breadth | 5/20 (25.00%) |
| Bootstrap P(mean stress return > 0) | 46.45% |
| Max Positive-Symbol Concentration | 44.12% |
| Selection Cutoff Violations | 0 |

### Breakdown of Gross Funding vs. Trading Fees:

| Cost Model | Gross Funding PnL | Trading Fees | Net PnL |
|---|---:|---:|---:|
| **Normal (1x cost)** | +1,460,396 VND | -741,145 VND | +719,251 VND |
| **Stress (2x cost)** | +1,436,488 VND | -1,454,106 VND | -17,617 VND |

Gross funding remains positive when costs increase, but turnover fees scale up enough to erase the entire theoretical edge. Stress edge retention is **-2.45%**, well below the required 50% threshold.

---

## 4. Multi-Year Fold Attribution

| OOS Fold | Selected Routes | Sufficient Sample | Normal Net PnL | Stress 2x Net PnL |
|---|---:|---:|---:|---:|
| **Y2024** | 6 | 5 | +653,238 VND | +467,760 VND |
| **Y2025** | 9 | 8 | +96,094 VND | -238,643 VND |
| **Y2026 (partial)** | 10 | 7 | -30,081 VND | -246,734 VND |

Positive performance was concentrated in 2024 and decayed rapidly thereafter. The edge lacks inter-temporal persistence: normal cost returns hovered near breakeven in 2025 and turned negative in 2026, while stress cost returns were negative across both recent periods.

Notable positive stress-cost folds included PEPE 2024 (+29.99%), DOGE 2024 (+15.14%), YFI 2024 (+4.43%), ETH 2024 (+2.07%), and ZEC 2025 (+4.65%). However, PEPE, DOGE, ETH, and YFI all degraded to negative returns in subsequent years.

---

## 5. Selected Parameter Analysis

`L14D / T0BPS` accounted for 19 out of 25 selections. The training algorithm consistently favoured slower, smoother funding estimates and maintained active pair exposure whenever two venues were available, rather than demanding high spread thresholds. Higher thresholds reduced market exposure but resulted in statistically insufficient sample sizes.

---

## 6. Failure Modes & Research Gate Summary

The strategy failed five key quantitative robustness criteria:

1. **Negative Stress PnL:** Aggregate net PnL is negative under 2x transaction friction.
2. **Negative Stress Edge Retention:** -2.45%, failing the $\ge 50\%$ benchmark.
3. **Insufficient Breadth:** Only 25.00% of routes with sufficient data remained positive under stress, failing the $>50\%$ breadth requirement.
4. **Weak Bootstrap Probability:** 46.45% probability of positive mean return, far below the 95% statistical confidence gate.
5. **Excessive Concentration:** 44.12% of positive PnL came from a single symbol, exceeding the 25% concentration ceiling.
