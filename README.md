# 📊 Stock Trend Dashboard (HOSE)

Dashboard phân tích kỹ thuật và mô hình giao dịch theo trend cho cổ phiếu niêm yết trên HOSE.

## ✨ Tính năng

- **Tín hiệu 3 khung thời gian**: ngắn hạn (15 phút), trung hạn (ngày), dài hạn (quý)
- **Đa mã**: gõ bất kỳ mã HOSE nào (VIX, SSI, VND...) để phân tích
- **Backtest minh bạch**: đường cong tài sản chiến lược vs mua-nắm-giữ, đã trừ phí giao dịch
- **Kịch bản tương lai**: ngoại suy trend + biên dao động hiệu chỉnh bằng sai số thực tế
- **Biểu đồ trực quan**: nến 15m/ngày, RSI(50), MA20/MA50, nhãn thời gian đầy đủ, đường chỉ giờ khi hover

## 🚀 Cài đặt

Yêu cầu: Python 3.10+

```bash
pip install -r requirements.txt
```

Chi tiết từng bước cho Windows: xem [HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md).

## ▶️ Sử dụng

**Windows:** bấm đúp `Mo_Dashboard.bat` (trình duyệt tự mở)

**Hoặc dòng lệnh:**

```bash
streamlit run dashboard.py
```

Mở trình duyệt tại `http://localhost:8501`. Dữ liệu tự refresh mỗi 15 phút.

## 📐 Mô hình

| Khung | Tín hiệu | Quy tắc |
|---|---|---|
| Ngắn hạn (15m) | BEARISH / BULLISH / NEUTRAL | RSI(50) vượt 53 → momentum đủ mạnh để canh mua |
| Trung hạn (ngày) | BULLISH / DEFENSIVE | Nắm giữ khi Giá > MA50 **và** VN-Index > MA50, còn lại giữ tiền |
| Dài hạn (quý) | Scorecard | Đánh giá cơ bản theo quý (xem `KHUNG_DAI_HAN.md`) |

### Kế hoạch giao dịch (khung trung hạn)

1. Mỗi sáng mở dashboard, xem thẻ **"Trung hạn (ngày)"**
2. Chỉ hành động khi tín hiệu **đổi trạng thái** (BULLISH ↔ DEFENSIVE)
3. Dùng giá đóng cửa tính tín hiệu, mua/bán vào phiên sáng hôm sau
4. Tần suất: ~15 vòng mua-bán / 800 ngày (trung bình 2 tháng một lần)

### Kết quả backtest (VIX, 800 ngày, đã trừ phí 0.4%/vòng)

|  | Chiến lược trend | Mua-nắm-giữ |
|---|---|---|
| Tổng lợi nhuận | **+130.9%** | +22.1% |
| Sharpe | 1.11 | 0.35 |
| Drawdown sâu nhất | -33.8% | -64.9% |
| Thời gian nắm giữ | 38% | 100% |
| Độ chính xác quyết định/ngày | 55.0% | 46.1% (baseline) |

> ⚠️ Backtest là quá khứ, không đảm bảo tương lai. Mô hình ngắn hạn (15m) test độc lập
> **không có lãi** sau chi phí — chỉ dùng để canh điểm vào khi trung hạn BULLISH.
> Kết quả trên mới chỉ kiểm chứng trên VIX; mỗi mã khác cần kiểm chứng riêng.

## 📁 Cấu trúc thư mục

```
├── dashboard.py           # Dashboard Streamlit (file chính)
├── Mo_Dashboard.bat       # Bấm đúp để mở dashboard (Windows)
├── vix_model.py           # Mô hình 3 khung + backtest
├── lam_moi_du_lieu.py     # Tải dữ liệu mới từ Vietcap API
├── requirements.txt       # Thư viện Python cần thiết
├── BAO_CAO_MO_HINH.md     # Báo cáo backtest chi tiết
├── KHUNG_DAI_HAN.md       # Scorecard khung dài hạn
└── HUONG_DAN_SU_DUNG.md   # Hướng dẫn sử dụng chi tiết
```

## ⚖️ Miễn trừ trách nhiệm

Đây là công cụ phân tích kỹ thuật, **không phải khuyến nghị đầu tư**.
Mọi quyết định giao dịch là trách nhiệm của người dùng. Không dùng margin
với bất kỳ tín hiệu nào từ công cụ này.
