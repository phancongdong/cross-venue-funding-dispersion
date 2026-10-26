# Strategy Guide: Cross-Venue Funding Rate Dispersion

---

## 1. Core Mathematical Mechanism

The **Cross-Venue Funding Dispersion** strategy is a market-neutral, delta-neutral quantitative model that exploits structural funding rate discrepancies across multiple perpetual swap exchanges (Bybit, OKX, Hyperliquid) for identical underlying assets.

### Perpetual Swap Funding Payment Mechanics:
* **Funding Rate > 0** (Bullish premium): Long positions pay Short positions.
* **Funding Rate < 0** (Bearish discount): Short positions pay Long positions.

### Delta-Neutral Pair Selection Rule:
At each daily decision point (`00:00 UTC`):
1. **Compute Trailing Funding Rate** over a rolling window $L \in \{1, 3, 7, 14\}$ days for each candidate venue:
   $$\text{Rate}_{\text{daily}}(v) = \frac{\sum_{t \in [T - L, T)} \text{funding\_rate}(v, t)}{L}$$
2. **Select Long Leg:** The venue with the lowest (or most negative) trailing rate:
   $$v_{\text{long}} = \arg\min_{v} \text{Rate}_{\text{daily}}(v)$$
3. **Select Short Leg:** The venue with the highest trailing rate:
   $$v_{\text{short}} = \arg\max_{v} \text{Rate}_{\text{daily}}(v)$$
4. **Forecast Annualized Spread:**
   $$\text{Spread (bps/day)} = \left(\text{Rate}_{\text{daily}}(v_{\text{short}}) - \text{Rate}_{\text{daily}}(v_{\text{long}})\right) \times 10{,}000$$
5. **Entry & Position Filter:**
   * A pair position is only opened if $\text{Spread} \ge \text{Threshold}$ ($0, 2,$ or $5\text{ bps/day}$).
   * Both venues must satisfy the 12-hour staleness guard.
   * If the spread drops below threshold or data goes stale, the position is closed to cash.

---

## 2. Why Does This Strategy Require Very High Capital?

While the theoretical concept appears straightforward, live implementation imposes severe capital barriers:

### a. Margin Fragmentation Across Independent Venues
* Capital cannot be pooled under a single unified margin account. Collateral must be deposited and locked across **three independent exchanges** (Bybit, OKX, Hyperliquid).
* Cross-exchange margin offsetting is not possible natively. Unused margin buffer must sit idle on each exchange to prevent forced liquidation during rapid, one-sided price swings.

### b. Thin Spreads vs. Double Taker Fees
* Every position rebalance requires executing two separate legs (1 Long on Venue A, 1 Short on Venue B), incurring **two-sided taker fees**:
  * Round-trip trading friction $\approx 2 \times 0.05\% = 0.10\%$ ($10\text{ bps}$).
  * Meanwhile, typical daily funding rate spreads average only $0.01\% - 0.04\%$/day ($1 - 4\text{ bps}$).
* For small accounts, cumulative daily dollar yields are minuscule and get consumed by turnover fees whenever the optimal pair shifts. Substantial capital ($>\$200{,}000$) is required so that the absolute yield significantly outweighs execution costs.

### c. Basis Risk and Execution Slippage
* Perpetual swap mark prices between Bybit, OKX, and Hyperliquid do not trade at perfect tick parity. Temporary basis divergence can inflict temporary unrealized mark-to-market drawdowns on the hedged spread.
* Sufficient capital buffers are mandatory to weather basis volatility without triggering margin calls before funding accruals materialize.

---

## 3. Empirical Research Findings & Failure Modes

In the formal Out-Of-Sample walk-forward study (Y2024 – Y2026):
* **Normal Cost (5 bps/leg):** Aggregate net PnL was positive at **+719,251 VND** (Gross funding PnL: $+1,460,396\text{ VND}$, Fees: $-741,145\text{ VND}$).
* **Stress Cost (10 bps/leg / 2x cost):** Aggregate net PnL collapsed to **negative: -17,617 VND** (Gross funding $+1,436,488\text{ VND}$ was fully absorbed by $-1,454,106\text{ VND}$ in turnover fees).
* **Quantitative Verdict:** `FUNDING_DISPERSION_REJECTED_HISTORICAL`.
* **Root Cause:** Rebalance turnover frequency was too high relative to the modest magnitude of cross-venue funding dispersion, making the edge vulnerable to execution friction.
