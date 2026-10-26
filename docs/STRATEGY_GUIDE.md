# Hướng Dẫn Chiến Lược: Giao Dịch Chênh Lệch Funding Rate Đa Sàn (Cross-Venue Funding Dispersion)

---

## 1. Cơ Chế Thuật Toán (Core Mechanism)

Chiến lược **Cross-Venue Funding Dispersion** là mô hình giao dịch định lượng trung hòa thị trường (Market Neutral / Delta-Neutral) khai thác sự lệch pha trong tỷ lệ Funding Rate giữa các sàn giao dịch phái sinh (Bybit, OKX, Hyperliquid) trên cùng một tài sản cơ sở.

### Nguyên lý thanh toán Funding Rate trên thị trường phái sinh:
* Nếu **Funding Rate > 0** (thị trường Bullish): Phe Long trả tiền cho phe Short.
* Nếu **Funding Rate < 0** (thị trường Bearish): Phe Short trả tiền cho phe Long.

### Quy tắc ghép cặp (Long/Short Pair Selection):
Tại mỗi chu kỳ quyết định (hàng ngày lúc `00:00 UTC`):
1. **Tính tỷ lệ funding trung bình động (Trailing Funding Rate)** trên cửa sổ $L \in \{1, 3, 7, 14\}$ ngày cho từng sàn:
   $$\text{Rate}_{\text{daily}}(v) = \frac{\sum_{t \in [T - L, T)} \text{funding\_rate}(v, t)}{L}$$
2. **Chọn chân Long (Long Leg):** Sàn có trailing rate thấp nhất (hoặc âm sâu nhất):
   $$v_{\text{long}} = \arg\min_{v} \text{Rate}_{\text{daily}}(v)$$
3. **Chọn chân Short (Short Leg):** Sàn có trailing rate cao nhất (dương lớn nhất):
   $$v_{\text{short}} = \arg\max_{v} \text{Rate}_{\text{daily}}(v)$$
4. **Dự báo chênh lệch lợi nhuận (Forecast Spread):**
   $$\text{Spread (bps/day)} = \left(\text{Rate}_{\text{daily}}(v_{\text{short}}) - \text{Rate}_{\text{daily}}(v_{\text{long}})\right) \times 10{,}000$$
5. **Điều kiện mở vị thế (Threshold Filter):**
   * Vị thế chỉ được kích hoạt nếu $\text{Spread} \ge \text{Threshold}$ ($0, 2,$ hoặc $5\text{ bps/ngày}$).
   * Cả 2 sàn đều phải có dữ liệu mới trong vòng 12 giờ (Stale Guard).

---

## 2. Vì Sao Chiến Lược Này Cần Vốn Rất Cao?

Chiến lược này thường được các quỹ định lượng hoặc nhà đầu tư có số vốn lớn áp dụng vì 4 rào cản vốn then chốt:

### a. Phân mảnh ký quỹ (Margin Fragmentation)
* Không giống như giao dịch trên một sàn đơn lẻ, bạn phải chia vốn và nạp ký quỹ vào **3 sàn giao dịch độc lập** (Bybit, OKX, Hyperliquid).
* Vốn ở sàn này không thể bù trừ ký quỹ (cross-margin) cho sàn kia. Bạn phải duy trì lượng tiền mặt dự phòng lớn ở cả hai phía để tránh việc một bên bị thanh lý cưỡng bức (forced liquidation) khi giá coin tăng hoặc giảm sốc.

### b. Tỷ suất lợi nhuận mỏng so với phí giao dịch (Low Yield vs. Double Fees)
* Mỗi lần vào/thoát vị thế, hệ thống phải thực hiện 2 lệnh (1 lệnh Long ở sàn A, 1 lệnh Short ở sàn B), tốn **phí giao dịch 2 đầu (Taker Fees)**:
  * Chi phí 1 vòng (Round-trip fee) $\approx 2 \times 0.05\% = 0.10\%$ ($10\text{ bps}$).
  * Trong khi chênh lệch funding rate thông thường chỉ dao động từ $0.01\% - 0.04\%$/ngày.
* Nếu vốn nhỏ (vài nghìn USD), số tiền funding thu về mỗi ngày rất ít, không đủ bù phí giao dịch khi cặp sàn đảo chiều và phải chuyển vị thế. Quy mô vốn phải từ hàng trăm nghìn USD trở lên thì giá trị tuyệt đối của phần chênh lệch mới đủ lớn.

### c. Rủi ro lệch giá cơ sở (Basis Risk & Slippage)
* Giá giao dịch thực tế giữa Bybit, OKX và Hyperliquid không hoàn toàn bằng nhau mọi giây (Basis Discrepancy). 
* Khi thị trường biến động mạnh, chân Short ở một sàn có thể lỗ sâu hơn chân Long ở sàn còn lại. Cần đệm vốn dày để giữ trạng thái delta-neutral mà không bị chạm ngưỡng margin call.

---

## 3. Kết Quả Kiểm Định Lịch Sử & Nguyên Nhân Thất Bại

Trong bài kiểm định Out-Of-Sample (2024 – 2026):
* **Chi phí thường (5 bps/leg):** Tổng PnL đạt **+719,251 VND** (Lợi nhuận gộp từ funding là $+1,460,396\text{ VND}$, phí giao dịch mất $-741,145\text{ VND}$).
* **Chi phí Stress 2x (10 bps/leg):** Tổng PnL rơi xuống mức **âm: -17,617 VND** (Lợi nhuận funding $+1,436,488\text{ VND}$ bị phí giao dịch $-1,454,106\text{ VND}$ nuốt trọn).
* **Kết luận định lượng:** `FUNDING_DISPERSION_REJECTED_HISTORICAL`.
* **Lý do:** Tần suất đảo vị thế (turnover) cao khiến chi phí vào/thoát lệnh triệt tiêu toàn bộ phần chênh lệch funding rate kiếm được.
