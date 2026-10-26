# Nghiên cứu Cross-Venue Funding Dispersion

Ngày nghiên cứu: 2026-08-02 (Asia/Saigon)

Phạm vi: `LOCAL/RESEARCH/HISTORICAL_POST_SELECTED`.

Live authority: `NONE`. Deployment permitted: `false`.

## 1. Kết luận

Phương pháp mua perpetual ở venue có funding thấp nhất và bán cùng symbol ở
venue có funding cao nhất không vượt qua frozen gate. Verdict:

`FUNDING_DISPERSION_REJECTED_HISTORICAL`.

Chênh lệch funding có tồn tại và tạo gross funding dương, nhưng không bền qua
regime và quá nhạy với turnover cost. Đây còn là funding-only replay: chưa có
basis PnL, mark-price divergence, order book, latency, margin fragmentation và
liquidation. Vì vậy ngay cả kết quả normal dương cũng không phải bằng chứng có
thể giao dịch thực tế.

## 2. Phương pháp đã khóa

- 11 symbol có ít nhất hai venue trong OKX, Bybit và Hyperliquid.
- Dữ liệu event-level: 30 parquet thuộc bộ Phase-3 đã verify SHA-256/CRC.
- Quyết định mỗi ngày lúc `00:00 UTC`; execution trễ một giờ.
- Long venue có trailing funding thấp nhất, short venue cao nhất, mỗi leg 1x
  equity; tổng gross leverage 2x, dưới cap 3x.
- Hourly fail-closed khi funding feed stale quá 12 giờ.
- 12 candidate: lookback `1/3/7/14` ngày x threshold `0/2/5` bps mỗi ngày.
- Expanding train và locked OOS folds 2024, 2025, 2026 partial.
- Normal cost 5 bps cho mỗi one-way leg action; stress exact 2x là 10 bps.
- Tài khoản độc lập 1 triệu VND cho mỗi symbol/fold; không có shared-portfolio
  claim.

Phương pháp này không dùng khung nến. Timeframe vận hành là daily decision với
hourly freshness monitoring và funding event theo cadence thật 1h/4h/8h của
từng venue.

## 3. Kết quả chính

| Chỉ tiêu | Kết quả |
|---|---:|
| Train-grid rows | 396 |
| Fold selections | 33 |
| Selected symbol/folds | 25 |
| Đủ ít nhất 30 active OOS days | 20 |
| Normal PnL | +719,251 VND |
| Stress 2x PnL | -17,617 VND |
| Positive stress breadth | 5/20 (25.00%) |
| Bootstrap P(mean stress return > 0) | 46.45% |
| Max positive-symbol concentration | 44.12% |
| Selection cutoff violations | 0 |

Funding và phí trên 25 selected paths:

| Cost model | Gross funding PnL | Fees | Net PnL |
|---|---:|---:|---:|
| Normal | +1,460,396 | -741,145 | +719,251 |
| Stress 2x | +1,436,488 | -1,454,106 | -17,617 |

Gross funding không mất hoàn toàn khi tăng phí, nhưng turnover cost tăng đủ để
xóa toàn bộ edge. Stress edge retention là -2.45%, thấp hơn gate 50%.

## 4. Phân rã theo thời gian

| OOS fold | Selected | Đủ sample | Normal PnL | Stress 2x PnL |
|---|---:|---:|---:|---:|
| 2024 | 6 | 5 | +653,238 | +467,760 |
| 2025 | 9 | 8 | +96,094 | -238,643 |
| 2026 partial | 10 | 7 | -30,081 | -246,734 |

Kết quả dương tập trung ở 2024 rồi suy giảm rõ. Đây không phải edge ổn định:
normal gần hòa vốn trong 2025 và âm trong 2026, còn stress âm ở cả hai giai đoạn
gần nhất.

Các fold stress nổi bật dương gồm PEPE 2024 (+29.99%), DOGE 2024 (+15.14%),
YFI 2024 (+4.43%), ETH 2024 (+2.07%) và ZEC 2025 (+4.65%). Tuy nhiên PEPE,
DOGE, ETH và YFI đều chuyển âm trong 2025 hoặc 2026. Không được chọn lại riêng
các symbol/fold thắng sau khi đã thấy kết quả.

## 5. Candidate được chọn

`L14D/T0BPS` chiếm 19/25 selections. Kết quả này cho thấy train thường ưu tiên
một estimate funding chậm và luôn giữ pair khi có đủ hai venue, thay vì một
threshold chênh lệch cao. Các threshold lớn hơn giảm exposure nhưng thường tạo
sample nhỏ: MEW 2026 chỉ 22 active days, WLD 2025 chỉ 11 ngày và WLD 2026 không
có active day.

## 6. Vì sao phương pháp bị loại

Frozen gate thất bại ở năm điểm:

1. Stress 2x tổng hợp âm.
2. Stress edge retention âm, không đạt 50%.
3. Chỉ 25% sufficient symbol/folds dương ở stress, không đạt breadth >50%.
4. Bootstrap probability 46.45%, rất xa gate 95%.
5. Positive PnL concentration 44.12%, vượt cap 25%.

Ngoài các failure định lượng, replay chưa tính basis. Một cặp delta-neutral theo
notional vẫn có thể lỗ khi giá perpetual hai venue phân kỳ giữa entry và exit.
Do đó không được diễn giải normal PnL dương là arbitrage có thể thực thi.

## 7. Quyết định nghiên cứu

- Archive universal cross-venue funding dispersion dưới nhãn
  `FUNDING_DISPERSION_REJECTED_HISTORICAL`.
- Không giảm phí, bỏ stale guard, chọn riêng PEPE/DOGE 2024 hoặc thay threshold
  sau kết quả để cứu thesis này.
- Không route paper/live và không tăng risk.
- Chỉ mở study mới nếu có synchronized venue-native mark/index prices, bid/ask,
  fee tier, execution latency và margin/liquidation model. Study đó phải được
  freeze mới và bắt đầu bằng prospective data; không được coi là continuation
  OOS của kết quả hiện tại.

## 8. Artifacts và provenance

- Spec: `research/CROSS_VENUE_FUNDING_DISPERSION_PIT_WF_SPEC_20260802.md`,
  SHA-256 `E2B8D1B6A2B6E72252A31F5449111822030F018E01AEF6434FC89C63201D8D6E`.
- Runner: `scripts/research_cross_venue_funding_dispersion_pit_wf_20260802.py`,
  SHA-256 `E3E597BCD5C52A87F73CF3218EEB6DD16D01E926BA3ADB3ECE155EFF55DE9BC5`.
- Results: `research/CROSS_VENUE_FUNDING_DISPERSION_PIT_WF_RESULTS_20260802.md`,
  SHA-256 `5153876603CEEF79A0ECFCD82840D7CE6F89788502083BAEEF30C012591D98CA`.
- Summary: `data/cross_venue_funding_dispersion_pit_wf_20260802/summary.json`,
  SHA-256 `A2DA8F725DDD81ADF98E28F09ADFA4402F572E8813FB361F87E81B16E2E7E0F7`.
- Test: `tests/test_research_cross_venue_funding_dispersion_pit_wf_20260802.py`.

Artifact inventory có 8 file, không tự hash `artifact_hashes.json`. Có 11,552
OOS daily rows, 1,182 OOS pair episodes và không có selection cutoff violation.
