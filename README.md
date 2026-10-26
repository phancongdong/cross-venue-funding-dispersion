# Giao Dịch Chênh Lệch Funding Rate Đa Sàn (Cross-Venue Funding Dispersion)

Gói mã nguồn và tài liệu nghiên cứu định lượng độc lập về chiến lược **Giao dịch chênh lệch Funding Rate giữa các sàn phái sinh (Bybit, OKX, Hyperliquid)**.

> **Lưu ý quy chuẩn:** Gói này được trích xuất hoàn toàn độc lập, **KHÔNG chứa hệ thống kiểm định 7-gate (7gate)** và **KHÔNG chứa các thuật toán giao dịch khác** (như Fibonacci, SMC, Breakout, Trend Following,...).

---

## 1. Cấu Trúc Thư Mục

```text
C:\cross_venue_funding_dispersion\
│
├── README.md                                    # Hướng dẫn tổng quan & khởi chạy
├── requirements.txt                             # Danh sách thư viện Python cần thiết
├── run_backtest.py                              # CLI runner độc lập để chạy backtest
│
├── docs/                                        # Toàn bộ tài liệu nghiên cứu gốc
│   ├── CROSS_VENUE_FUNDING_DISPERSION_SYNTHESIS_VI.md # Báo cáo tổng hợp kết quả (Tiếng Việt)
│   ├── CROSS_VENUE_FUNDING_DISPERSION_SPEC.md         # Quy chuẩn kỹ thuật chi tiết
│   ├── CROSS_VENUE_FUNDING_DISPERSION_RESULTS.md      # Báo cáo chi tiết theo từng fold/cặp tiền
│   ├── STRATEGY_GUIDE.md                              # Phân tích cơ chế & lý do cần vốn lớn
│   └── DATA_SCHEMA.md                                 # Đặc tả dữ liệu funding rate đa sàn
│
├── src/                                         # Mã nguồn thuật toán thuần túy
│   ├── __init__.py
│   ├── config.py                                # Cấu hình sàn, cặp tiền, chi phí, mốc thời gian
│   ├── models.py                                # Cấu trúc dữ liệu (VenueSeries, Candidate, PairTarget)
│   ├── data_loader.py                           # Module nạp & tiền xử lý Parquet funding rate
│   ├── signal_engine.py                         # Thuật toán tính trailing funding, ranking & tạo tín hiệu
│   ├── simulator.py                             # Engine mô phỏng PnL, tính funding payment & phí chuyển vị thế
│   ├── walk_forward.py                          # Thuật toán Walk-Forward Optimization độc lập
│   └── analytics.py                             # Tính toán chỉ số PnL, DD, Sharpe, Bootstrap
│
├── tests/                                       # Bộ Unit Test kiểm tra tính đúng đắn thuật toán
│   ├── __init__.py
│   └── test_funding_dispersion.py               # 7 test cases độc lập
│
└── data/                                        # Dữ liệu mẫu & Parquet lịch sử
    └── datasets/cross_venue_funding/
        ├── bybit/                               # 11 cặp tiền phái sinh Bybit
        ├── hyperliquid/                         # 10 cặp tiền phái sinh Hyperliquid
        └── okx/                                 # 12 cặp tiền phái sinh OKX
```

---

## 2. Cài Đặt Môi Trường

Yêu cầu Python $\ge 3.10$:

```bash
pip install -r requirements.txt
```

---

## 3. Hướng Dẫn Sử Dụng

### Chạy backtest trên 1 cặp tiền cụ thể (ví dụ ETHUSDT):
```bash
# Chạy với chi phí chuẩn (5 bps / leg):
python run_backtest.py --symbol ETHUSDT --lookback 14 --threshold 0

# Chạy với chi phí stress 2x (10 bps / leg):
python run_backtest.py --symbol ETHUSDT --lookback 14 --threshold 0 --stress-cost
```

### Chạy kiểm định Walk-Forward toàn bộ danh mục:
```bash
python run_backtest.py --walk-forward
```

### Chạy kiểm tra Unit Test:
```bash
pytest tests/test_funding_dispersion.py -v
```

---

## 4. Tóm Tắt Thuật Toán & Cơ Chế Hoạt Động

1. **Chu kỳ quyết định (Daily Cadence):** Thực hiện tính toán hàng ngày vào lúc `00:00 UTC`, lệnh được kích hoạt vào `01:00 UTC` (trễ 1 giờ).
2. **Cửa sổ tính toán (Trailing Window):** Đánh giá tổng funding rate trong quá khứ theo các khung $L \in \{1, 3, 7, 14\}$ ngày.
3. **Lựa chọn chân vị thế (Delta-Neutral Selection):**
   * **Long:** Sàn có funding rate thấp nhất (hoặc âm sâu nhất).
   * **Short:** Sàn có funding rate cao nhất.
4. **Bộ lọc chênh lệch (Spread Threshold):** Chỉ mở vị thế khi mức chênh lệch dự kiến $\ge \text{Threshold}$ ($0, 2, 5\text{ bps/ngày}$).
5. **Cơ chế phòng hộ mất kết nối (Staleness Guard):** Nếu dữ liệu của một trong hai sàn trễ quá **12 giờ**, hệ thống tự động thoát vị thế về tiền mặt (`DAILY_CASH` / `STALE_EXIT`).
6. **Mô hình chi phí thực tế:** Phí giao dịch được trừ chính xác theo từng chân thay đổi ($0, 1, 2$ chân mở/đóng/đảo chiều).

---

## 5. Kết Luận Nghiên Cứu Định Lượng

* **Lợi nhuận gộp từ Funding Rate:** Thực tế có tồn tại chênh lệch funding rate dương giữa Bybit, OKX và Hyperliquid (tạo ra $+1,460,396\text{ VND}$ gross funding trên các mẫu kiểm định).
* **Rào cản chi phí:** Tuy nhiên, tần suất đảo vị thế (turnover) tương đối cao khiến chi phí giao dịch nuốt trọn lợi nhuận ở kịch bản Stress 2x (tổng PnL stress âm $-17,617\text{ VND}$).
* **Rào cản vốn lớn:** Yêu cầu lượng vốn ban đầu rất cao do phải phân mảnh ký quỹ ở 3 sàn độc lập (margin fragmentation), duy trì bộ đệm tiền mặt lớn để phòng ngừa biến động lệch giá (basis divergence) mà không bị thanh lý một bên.
