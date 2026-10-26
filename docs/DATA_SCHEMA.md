# Đặc Tả Dữ Liệu Funding Rate Đa Sàn (Cross-Venue Funding Schema)

Tài liệu này quy chuẩn cấu trúc dữ liệu lịch sử funding rate của các sàn giao dịch hợp đồng tương lai vĩnh cửu (Perpetual Futures) được sử dụng trong nghiên cứu `CROSS_VENUE_FUNDING_DISPERSION`.

---

## 1. Các Sàn Giao Dịch & Chu Kỳ Funding (Funding Cadence)

Hệ thống hỗ trợ 3 sàn phái sinh lớn với chu kỳ thanh toán funding khác nhau:

| Sàn (Venue) | Loại hợp đồng | Chu kỳ Funding | Giờ thanh toán chuẩn (UTC) |
|---|---|---|---|
| **Bybit** | USDT-M Perpetual | 8 giờ / lần | `00:00`, `08:00`, `16:00` |
| **OKX** | USDT-M Swap | 8 giờ / lần | `00:00`, `08:00`, `16:00` |
| **Hyperliquid** | Native Perpetual (DEX L1) | 1 giờ / lần | Đầu mỗi giờ tròn |

---

## 2. Cấu Trúc File Parquet (`datasets/cross_venue_funding/{venue}/{symbol}.parquet`)

Mỗi file Parquet đại diện cho chuỗi sự kiện funding rate của một cặp giao dịch trên một sàn cụ thể.

### Các trường dữ liệu (Columns):

| Tên cột | Kiểu dữ liệu | Ý nghĩa | Ví dụ |
|---|---|---|---|
| `venue` | `string` | Tên sàn giao dịch | `"bybit"`, `"hyperliquid"`, `"okx"` |
| `aitrade_symbol` | `string` | Ký hiệu chuẩn hóa nội bộ | `"BTCUSDT"`, `"ETHUSDT"` |
| `venue_symbol` | `string` | Ký hiệu nguyên bản của sàn | `"BTC-USDT-SWAP"`, `"BTCUSDT"` |
| `funding_time_ms` | `int64` | Timestamp sự kiện tính bằng mili-giây (Unix Epoch) | `1672531200000` |
| `funding_time_utc` | `string` / `timestamp` | Thời gian UTC chuẩn ISO 8601 | `"2023-01-01T00:00:00+00:00"` |
| `funding_rate` | `float64` | Tỷ lệ funding rate của chu kỳ (dạng số thập phân) | `0.0001` (tức 0.01% / chu kỳ) |
| `source_channel` | `string` | Kênh thu thập dữ liệu gốc | `"rest_history"`, `"archive"` |

---

## 3. Quy Tắc Toàn Vẹn & Đồng Bộ Dữ Liệu

1. **Tránh Lookahead Bias (Tính Causal Điểm Thời Gian):**
   * Quyết định vị thế được tính tại mốc `00:00 UTC` mỗi ngày.
   * Chỉ các sự kiện funding có `funding_time_utc < 00:00 UTC` mới được đưa vào công thức tính rolling funding rate.
2. **Cơ Chế Phát Hiện Mất Kết Nối / Dữ Liệu Cũ (Staleness Guard):**
   * Nếu sự kiện gần nhất của một sàn cũ hơn **12 giờ** so với thời điểm ra quyết định, sàn đó bị coi là mất kết nối (Stale).
   * Hệ thống sẽ tự động thoát vị thế (fail-closed) để phòng ngừa rủi ro mất cân bằng một chân vị thế.
3. **Độ Trễ Khớp Lệnh (Execution Delay):**
   * Tín hiệu tính toán tại `00:00 UTC`, lệnh được mô phỏng khớp vào `01:00 UTC` (trễ 1 giờ) để phản ánh độ trễ thực tế.
