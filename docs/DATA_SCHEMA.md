# Cross-Venue Funding Rate Data Schema

This document standardizes the historical funding rate data structure across perpetual swap venues used in the `CROSS_VENUE_FUNDING_DISPERSION` research package.

---

## 1. Supported Venues & Funding Cadence

The system supports three major derivative venues with distinct settlement frequencies:

| Venue | Contract Type | Funding Cadence | Settlement Timestamps (UTC) |
|---|---|---|---|
| **Bybit** | USDT-M Perpetual | 8 hours | `00:00`, `08:00`, `16:00` |
| **OKX** | USDT-M Swap | 8 hours | `00:00`, `08:00`, `16:00` |
| **Hyperliquid** | Native Perpetual (DEX L1) | 1 hour | Top of every hour (`:00`) |

---

## 2. Parquet File Schema (`datasets/cross_venue_funding/{venue}/{symbol}.parquet`)

Each Parquet file stores the chronological sequence of discrete funding payment events for a specific instrument on a specific venue.

### Field Definitions:

| Column Name | Data Type | Description | Example |
|---|---|---|---|
| `venue` | `string` | Exchange name | `"bybit"`, `"hyperliquid"`, `"okx"` |
| `aitrade_symbol` | `string` | Canonical unified symbol | `"BTCUSDT"`, `"ETHUSDT"` |
| `venue_symbol` | `string` | Venue-native instrument identifier | `"BTC-USDT-SWAP"`, `"BTCUSDT"` |
| `funding_time_ms` | `int64` | Unix Epoch timestamp in milliseconds | `1672531200000` |
| `funding_time_utc` | `string` / `timestamp` | ISO 8601 formatted UTC timestamp | `"2023-01-01T00:00:00+00:00"` |
| `funding_rate` | `float64` | Periodic funding rate in decimal format | `0.0001` (representing 0.01% / period) |
| `source_channel` | `string` | Ingestion source channel | `"rest_history"`, `"archive"` |

---

## 3. Data Integrity & Invariants

1. **Point-in-Time Causality:**
   * Rebalance decisions occur at `00:00 UTC` daily.
   * Only events with `funding_time_utc < 00:00 UTC` (strictly prior) are admissible for rolling forecast calculations.
2. **Staleness Guard (Fail-Closed):**
   * If the most recent funding event from any participating venue is older than **12 hours** relative to the decision timestamp, that venue is marked stale.
   * The system fails closed to cash or exits existing positions (`STALE_EXIT`) to prevent unhedged single-leg exposure.
3. **Execution Delay:**
   * Signals computed at `00:00 UTC` are simulated as filled at `01:00 UTC` (1-hour delay) to reflect real-world latency and order submission.
