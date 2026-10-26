# Cross-Venue Funding Dispersion - PIT Walk-Forward Results

Status: `LOCAL/RESEARCH/HISTORICAL_POST_SELECTED`.
Live authority: `NONE`. Deployment permitted: `false`.

Verdict: `FUNDING_DISPERSION_REJECTED_HISTORICAL`.

## Frozen Method

- Equal-notional 1x long lowest trailing-funding venue and 1x short highest venue.
- Daily 00:00 UTC decision, one-hour execution delay, hourly 12-hour stale guard.
- Twelve train candidates: 1/3/7/14-day lookback x 0/2/5 bps daily threshold.
- Normal 5 bps and exact 2x 10 bps per one-way leg action.
- Funding-only accounting; synchronized basis and price PnL are unavailable.

## Aggregate Selected OOS

- Selected symbol/folds: 25.
- Sufficient symbol/folds: 20.
- Normal PnL: 719,251 VND.
- Stress 2x PnL: -17,617 VND.
- Stress edge retention: -2.45%.
- Positive stress breadth: 5/20 (25.00%).
- Bootstrap P(mean stress fold return > 0): 46.45%.
- Maximum positive-symbol concentration: 44.12%.

## Fold Results

| Symbol | Fold | Selected candidate | Active days | Normal return | 2x return | Normal fees | Verdict |
|---|---|---|---:|---:|---:|---:|---|
| BTCUSDT | Y2024 | CASH | 0 | 0.000% | 0.000% | 0 | NO_ELIGIBLE_CANDIDATE |
| BTCUSDT | Y2025 | FUNDING_DISPERSION|L14D|T0BPS | 365 | 1.493% | -2.782% | 43,257 | NEGATIVE_AFTER_COSTS |
| BTCUSDT | Y2026 | FUNDING_DISPERSION|L14D|T0BPS | 212 | -2.535% | -6.172% | 37,466 | NEGATIVE_AFTER_COSTS |
| DOGEUSDT | Y2024 | FUNDING_DISPERSION|L14D|T0BPS | 366 | 20.320% | 15.137% | 49,684 | POSITIVE_FUNDING_ONLY |
| DOGEUSDT | Y2025 | FUNDING_DISPERSION|L14D|T0BPS | 365 | -1.708% | -7.714% | 62,185 | NEGATIVE_AFTER_COSTS |
| DOGEUSDT | Y2026 | FUNDING_DISPERSION|L14D|T2BPS | 19 | -0.235% | -0.634% | 3,996 | INSUFFICIENT_OOS_SAMPLE |
| ETHUSDT | Y2024 | FUNDING_DISPERSION|L14D|T0BPS | 366 | 6.240% | 2.071% | 41,587 | POSITIVE_FUNDING_ONLY |
| ETHUSDT | Y2025 | FUNDING_DISPERSION|L14D|T0BPS | 365 | 0.836% | -4.085% | 49,726 | NEGATIVE_AFTER_COSTS |
| ETHUSDT | Y2026 | FUNDING_DISPERSION|L14D|T0BPS | 212 | -1.817% | -5.197% | 34,643 | NEGATIVE_AFTER_COSTS |
| IOTAUSDT | Y2024 | FUNDING_DISPERSION|L14D|T0BPS | 366 | -0.664% | -4.851% | 42,796 | NEGATIVE_AFTER_COSTS |
| IOTAUSDT | Y2025 | FUNDING_DISPERSION|L14D|T0BPS | 365 | 1.906% | -2.388% | 43,704 | NEGATIVE_AFTER_COSTS |
| IOTAUSDT | Y2026 | FUNDING_DISPERSION|L14D|T0BPS | 212 | 0.224% | -3.130% | 33,903 | NEGATIVE_AFTER_COSTS |
| MEWUSDT | Y2024 | CASH | 0 | 0.000% | 0.000% | 0 | NO_ELIGIBLE_CANDIDATE |
| MEWUSDT | Y2025 | CASH | 0 | 0.000% | 0.000% | 0 | NO_ELIGIBLE_CANDIDATE |
| MEWUSDT | Y2026 | FUNDING_DISPERSION|L7D|T5BPS | 22 | 0.002% | -0.994% | 9,979 | INSUFFICIENT_OOS_SAMPLE |
| PEPEUSDT | Y2024 | FUNDING_DISPERSION|L7D|T2BPS | 305 | 32.887% | 29.991% | 25,488 | POSITIVE_FUNDING_ONLY |
| PEPEUSDT | Y2025 | FUNDING_DISPERSION|L7D|T2BPS | 191 | 1.459% | -2.330% | 38,381 | NEGATIVE_AFTER_COSTS |
| PEPEUSDT | Y2026 | FUNDING_DISPERSION|L14D|T0BPS | 212 | 1.170% | -0.239% | 13,972 | NEGATIVE_AFTER_COSTS |
| TAOUSDT | Y2024 | CASH | 0 | 0.000% | 0.000% | 0 | NO_ELIGIBLE_CANDIDATE |
| TAOUSDT | Y2025 | FUNDING_DISPERSION|L14D|T0BPS | 365 | 0.925% | -4.002% | 49,975 | NEGATIVE_AFTER_COSTS |
| TAOUSDT | Y2026 | FUNDING_DISPERSION|L14D|T0BPS | 212 | 0.064% | -3.381% | 35,206 | NEGATIVE_AFTER_COSTS |
| THETAUSDT | Y2024 | CASH | 0 | 0.000% | 0.000% | 0 | NO_ELIGIBLE_CANDIDATE |
| THETAUSDT | Y2025 | CASH | 0 | 0.000% | 0.000% | 0 | NO_ELIGIBLE_CANDIDATE |
| THETAUSDT | Y2026 | CASH | 0 | 0.000% | 0.000% | 0 | NO_ELIGIBLE_CANDIDATE |
| WLDUSDT | Y2024 | CASH | 0 | 0.000% | 0.000% | 0 | NO_ELIGIBLE_CANDIDATE |
| WLDUSDT | Y2025 | FUNDING_DISPERSION|L14D|T5BPS | 11 | -0.686% | -1.478% | 7,975 | INSUFFICIENT_OOS_SAMPLE |
| WLDUSDT | Y2026 | FUNDING_DISPERSION|L14D|T5BPS | 0 | 0.000% | 0.000% | 0 | INSUFFICIENT_OOS_SAMPLE |
| YFIUSDT | Y2024 | FUNDING_DISPERSION|L14D|T0BPS | 366 | 6.542% | 4.429% | 20,409 | POSITIVE_FUNDING_ONLY |
| YFIUSDT | Y2025 | FUNDING_DISPERSION|L14D|T0BPS | 365 | 0.002% | -3.732% | 38,565 | NEGATIVE_AFTER_COSTS |
| YFIUSDT | Y2026 | FUNDING_DISPERSION|L14D|T0BPS | 212 | -0.917% | -3.270% | 23,889 | NEGATIVE_AFTER_COSTS |
| ZECUSDT | Y2024 | FUNDING_DISPERSION|L14D|T0BPS | 0 | 0.000% | 0.000% | 0 | INSUFFICIENT_OOS_SAMPLE |
| ZECUSDT | Y2025 | FUNDING_DISPERSION|L14D|T0BPS | 90 | 5.383% | 4.647% | 7,112 | POSITIVE_FUNDING_ONLY |
| ZECUSDT | Y2026 | FUNDING_DISPERSION|L14D|T0BPS | 212 | 1.037% | -1.657% | 27,247 | NEGATIVE_AFTER_COSTS |

## Interpretation

A positive funding-only result would still omit cross-venue basis changes, mark-price divergence, order-book execution, venue-native fees, margin fragmentation and liquidation risk. It cannot authorize paper or live trading.

## Audit

- Train grid rows: 396.
- Selection rows: 33.
- OOS daily rows: 11552.
- OOS episode rows: 1182.
- Selection cutoff violations: 0.
