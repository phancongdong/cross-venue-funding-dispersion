# Cross-Venue Funding Dispersion PIT Walk-Forward Specification

Status: `FROZEN_BEFORE_RESULTS`.

Scope: `LOCAL/RESEARCH/HISTORICAL_POST_SELECTED`.

Live authority: `NONE`. Deployment permitted: `false`.

Freeze date: 2026-08-02 (Asia/Saigon).

## 1. Research Question

Test whether cross-venue funding-rate dispersion is persistent enough for an
equal-notional long/short perpetual pair to retain positive funding-only returns
after conservative turnover costs.

The mechanism is:

1. estimate each venue's trailing funding paid per day using only events already
   published before the decision time;
2. go long the venue with the lowest trailing funding and short the venue with
   the highest trailing funding for the same symbol;
3. keep both legs until the next causal daily decision changes the pair, the
   forecast spread falls below the frozen threshold, or a venue becomes stale.

This is not a complete arbitrage backtest. Synchronized mark-price basis,
entry/exit basis convergence, order-book depth, venue-specific fee tiers,
latency, margin fragmentation, liquidation, transfer and outage losses are not
available. The study can reject the mechanism, but a positive result can be no
stronger than `MECHANISM_WATCH_BASIS_BLOCKED`.

## 2. Frozen Data And Provenance

Read-only external root:

`C:/QUANT/GitHubFinance/20260801_phase3`

Authoritative source artifacts:

- `verification_summary.json`, SHA-256
  `b61339901074271beba07f8d1e673147a6201d28968ace39d5f4bf76353bc2ee`;
  status must be `PASS`, with 33 funding parquet files and 310,230 events.
- `artifact_manifest.csv`, SHA-256
  `d8652c675c5e1941af5e995b431cdef477cbd2d104d7ed3110960ae672be7f34`.
- `funding_coverage.csv`, SHA-256
  `9f9ed608407f727cc2dc27ed24c74994488e131b5d4d9831f8c289d15fa8371e`.
- `funding_gap_audit.csv`, SHA-256
  `faf6bbcccb2687bf16b32c686e731f72c482af53f944f04a4da1e2bf728c48f1`.
- `cross_venue_overlap_summary.csv`, SHA-256
  `e6f25a5df47bbb3b96fa9281e05b0e2f84123750e7595504e1c478261244763e`.
- `SYMBOL_MAPPING.csv`, SHA-256
  `e2be7a9827826867803aa0e40c0a6f6fc02db54dbb6377e5e0d8b794369ec764`.

Every selected parquet must match its row in `artifact_manifest.csv` by path,
byte count and SHA-256 before any result is computed.

Required parquet columns are `venue`, `aitrade_symbol`, `venue_symbol`,
`funding_time_ms`, `funding_time_utc`, `funding_rate` and `source_channel`.
Duplicate venue timestamps or non-finite funding rates are fatal.

## 3. Frozen Point-In-Time Universe

Only symbols with at least two verified venue series are included:

| Symbol | Frozen venues |
|---|---|
| BTCUSDT | bybit, hyperliquid, okx |
| DOGEUSDT | bybit, hyperliquid, okx |
| ETHUSDT | bybit, hyperliquid, okx |
| IOTAUSDT | bybit, hyperliquid, okx |
| MEWUSDT | bybit, hyperliquid, okx |
| PEPEUSDT | hyperliquid, okx |
| TAOUSDT | bybit, hyperliquid, okx |
| THETAUSDT | bybit, okx |
| WLDUSDT | bybit, hyperliquid, okx |
| YFIUSDT | bybit, okx |
| ZECUSDT | bybit, hyperliquid, okx |

No current membership is backfilled before a venue series begins. At every
decision, only venues with causal history and fresh data may participate.

## 4. Decision, Execution And Staleness Contract

- Decision cadence: daily at `00:00 UTC`.
- Signal data: funding events with timestamp strictly earlier than the decision.
- Execution delay: one hour. A target decided at `00:00` becomes active at
  `01:00 UTC`; the method cannot capture a funding event between decision and
  execution.
- Funding accounting: actual events at or after position activation and before
  the next position change are applied by exact timestamp and venue cadence.
- Positive funding means longs pay shorts. For equal leg notional, funding
  return is `short_venue_rate - long_venue_rate`.
- Gross exposure: 2x equity, with one 1x long leg and one 1x short leg. This is
  below the frozen 3x gross leverage cap.
- Venue freshness at a decision: the most recent event strictly before the
  decision must be no older than 12 hours.
- Each candidate also requires at least two events from each venue inside its
  trailing lookback.
- Hourly fail-closed guard: if either active venue's most recent event strictly
  before the hour is older than 12 hours, queue a close for the next hour and
  remain cash until a later valid daily decision.
- Missing events are never forward-filled or replaced with another venue.

## 5. Frozen Candidate Grid

Exactly 12 candidates are tested per symbol and fold:

- lookback days: `1`, `3`, `7`, `14`;
- minimum forecast dispersion: `0`, `2`, `5` bps per day.

At each decision:

1. sum each eligible venue's funding rates over `[decision-lookback, decision)`;
2. divide by the exact lookback day count;
3. choose the venue with the highest daily rate for the short leg and the venue
   with the lowest daily rate for the long leg;
4. hold cash when fewer than two venues are eligible or the high-minus-low
   forecast is below the candidate threshold.

Tie-break venue names lexicographically. Thresholds, lookbacks, staleness,
decision cadence, delay and tie-breaks may not change after results are seen.

## 6. Costs And Accounting

Each symbol/fold is a standalone account starting with 1,000,000 VND. There is
no shared-capital portfolio claim.

Normal cost is 5 bps per one-way leg action. Exact 2x stress cost is 10 bps per
one-way leg action.

Turnover actions are counted per venue and side:

- cash to one leg or one leg to cash: one action;
- same venue and same side: zero actions;
- same venue with a side flip: two actions;
- closing one pair and opening a disjoint pair: four actions.

All open legs are charged a final close at a train or OOS boundary. Fee cost and
funding PnL are applied to current equity. Daily mark-to-market price/basis PnL
is intentionally absent and must be reported as the central limitation.

## 7. PIT Walk-Forward Folds

Expanding train and locked annual OOS folds:

| Fold | Train end exclusive | OOS interval |
|---|---|---|
| Y2024 | 2024-01-01 00:00 UTC | 2024-01-01 to 2025-01-01 |
| Y2025 | 2025-01-01 00:00 UTC | 2025-01-01 to 2026-01-01 |
| Y2026 | 2026-01-01 00:00 UTC | 2026-01-01 to 2026-07-31 19:00 UTC |

Per symbol, training starts only after the second venue is available. A fold is
`NOT_ELIGIBLE` unless the symbol has at least 180 calendar days of causal common
history before the selection cutoff.

The selected candidate is fixed through the complete OOS fold. No OOS result
may change a candidate, threshold, venue or rule.

The Phase-3 report already exposed full-period descriptive dispersion, so every
fold is labeled `HISTORICAL_POST_SELECTED`, not untouched OOS.

## 8. Train Admission And Selection

A candidate is train-eligible under both normal and 2x costs only when:

- common causal train span is at least 180 days;
- active exposure covers at least 90 distinct calendar days;
- at least 12 completed pair episodes exist;
- final return is positive at normal and 2x costs;
- 2x daily-return profit factor is at least 1.00;
- at least half of non-empty calendar quarters have positive PnL at both costs.

Rank eligible candidates by:

1. higher 2x final return;
2. higher normal final return;
3. higher 2x daily-return profit factor;
4. fewer normal-cost turnover bps;
5. stable candidate ID.

If no candidate is eligible, the symbol/fold holds 100% cash.

## 9. Aggregate Historical Gate

The selected OOS paths pass the funding-only mechanism screen only when all are
true:

- at least five symbol/folds are selected and have at least 30 active OOS days;
- aggregate normal and 2x PnL are positive;
- 2x edge retention is at least 50% of normal PnL;
- more than half of sufficient symbol/folds have positive 2x PnL;
- bootstrap `P(mean 2x symbol/fold return > 0)` is at least 95%;
- no symbol contributes more than 25% of total positive normal PnL;
- there are zero train-selection cutoff violations.

Verdicts:

- all gates pass: `MECHANISM_WATCH_BASIS_BLOCKED`;
- any gate fails: `FUNDING_DISPERSION_REJECTED_HISTORICAL`;
- no train candidate is selected: `NO_ELIGIBLE_FUNDING_DISPERSION`.

No verdict grants paper/live authority. A future tradability study would need
synchronized mark/index prices, basis PnL, venue-native fee tiers, order books,
margin/liquidation rules and outage handling frozen before results.

## 10. Required Artifacts

The runner must write:

- complete train grid, including rejected candidates;
- fold selections and rejection reasons;
- selected OOS fold metrics under normal and exact 2x costs;
- daily returns, pair episodes, turnover and stale-exit audits;
- coverage and parquet provenance;
- bootstrap diagnostics, gate checks and limitations;
- deterministic `summary.json`, results report and artifact hash inventory.

The artifact inventory must never include or hash its own previous
`artifact_hashes.json` copy.
