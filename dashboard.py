"""Stock Dashboard — mo len la thay tin hieu 3 khung thoi gian.
Chay local:  streamlit run dashboard.py
Deploy free: day len GitHub -> noi vao Streamlit Community Cloud.
"""
import time
import requests
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Dashboard", layout="wide")

VER = "3.1"  # tang so nay moi khi sua code -> biet chac dang chay ban nao
ticker = st.text_input("Mã cổ phiếu (HOSE)", value="VIX",
                       max_chars=10).strip().upper() or "VIX"

URL = "https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart"
H = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
COST = 0.004


@st.cache_data(ttl=900)
def fetch(symbol, timeframe, count_back, price_div=1):
    payload = {"timeFrame": timeframe, "symbols": [symbol],
               "to": int(time.time()) + 86400, "countBack": count_back}
    r = requests.post(URL, headers=H, json=payload, timeout=90)
    r.raise_for_status()
    d = r.json()
    d = d["data"] if isinstance(d, dict) and "data" in d else d
    s = d[0]
    df = pd.DataFrame({"t": s["t"], "o": s["o"], "h": s["h"],
                       "l": s["l"], "c": s["c"], "v": s["v"]})
    df["time"] = pd.to_datetime(df["t"].astype("int64"), unit="s",
                                utc=True).dt.tz_convert("Asia/Ho_Chi_Minh")
    df = df.set_index("time").sort_index()
    for col in ["o", "h", "l", "c"]:
        df[col] = df[col] / price_div
    return df[["o", "h", "l", "c", "v"]]


def rsi_wilder(close, period=50):
    d = close.diff()
    g = d.clip(lower=0).ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    l = (-d.clip(upper=0)).ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return 100 - 100 / (1 + g / l)


# ---------------------------------------------------------------- data
try:
    with st.spinner(f"Dang tai du lieu {ticker}..."):
        m1 = fetch(ticker, "ONE_MINUTE", 20000, 1000)
        dly = fetch(ticker, "ONE_DAY", 800, 1000)
        vni = fetch("VNINDEX", "ONE_DAY", 800, 1)
except Exception:
    st.error(f"Không tải được dữ liệu cho mã {ticker}. Kiểm tra lại mã CK.")
    st.stop()
if dly.empty or len(dly) < 60:
    st.error(f"Dữ liệu {ticker} không đủ (cần tối thiểu 60 ngày).")
    st.stop()

m15 = m1.resample("15min").agg(
    {"o": "first", "h": "max", "l": "min", "c": "last", "v": "sum"}).dropna()
dly["ma20"] = dly["c"].rolling(20).mean()
dly["ma50"] = dly["c"].rolling(50).mean()
vni["ma50"] = vni["c"].rolling(50).mean()
rsi50 = rsi_wilder(m15["c"], 50)

last = dly.iloc[-1]
bull_mt = (last["c"] > dly["ma50"].iloc[-1]) and (vni["c"].iloc[-1] > vni["ma50"].iloc[-1])
bear_st = last["c"] < dly["ma20"].iloc[-1]

# ---------------------------------------------------------------- header
st.title(f"{ticker} Dashboard — v{VER}")
st.caption(f"Cap nhat: {pd.Timestamp.now(tz='Asia/Ho_Chi_Minh'):%d/%m/%Y %H:%M} "
           f"| Gia hien tai: {last['c']:.2f}")

c1, c2, c3 = st.columns(3)
c1.metric("Ngan han (15m)",
          "BEARISH - Dung ngoai" if bear_st else
          ("BULLISH - Canh mua" if rsi50.iloc[-1] > 53 else "NEUTRAL - Cho tin hieu"),
          f"RSI(50) 15m = {rsi50.iloc[-1]:.1f}")
c2.metric("Trung han (ngay)",
          "BULLISH - Nam giu" if bull_mt else "DEFENSIVE - Giu tien",
          f"{ticker} {last['c']:.2f} vs MA50 {dly['ma50'].iloc[-1]:.2f}")
c3.metric("Dai han (quy)",
          "Xem scorecard",
          "KHUNG_DAI_HAN.md")

# ------------------------------------------------- how trend is predicted
with st.expander("Trend duoc du doan nhu the nao? (giai thich mo hinh)"):
    st.markdown(f"""
- **Trung han (mô hình chính):** nắm giữ {ticker} khi **giá > MA50 ngày ĐỒNG THỜI
  VN-Index > MA50 ngày**, còn lại giữ tiền mặt. Backtest 800 ngày trên VIX:
  **+130.9%** so với mua-nắm-giữ +19.5% (đã trừ phí). *Mỗi mã cần kiểm chứng riêng.*
- **Ngắn hạn:** momentum 15m (RSI(50) vượt 53) — test độc lập **không có lãi**
  sau chi phí → chỉ dùng để *canh điểm vào* khi trung hạn BULLISH.
- **Dài hạn:** scorecard cơ bản theo quý — không dự báo điểm số, chỉ quản trị kịch bản.
""")

# ---------------------------------------------------------------- charts
tab1, tab2, tab3, tab4 = st.tabs(["Gia & Trend (ngay)", "Hieu qua chien luoc",
                                    "15m gan day", "Kich ban tuong lai"])

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=dly.index, open=dly["o"], high=dly["h"],
                                 low=dly["l"], close=dly["c"], name=ticker))
    fig.add_trace(go.Scatter(x=dly.index, y=dly["ma20"], name="MA20",
                             line=dict(color="orange", width=1)))
    fig.add_trace(go.Scatter(x=dly.index, y=dly["ma50"], name="MA50",
                             line=dict(color="blue", width=1.5)))
    fig.update_layout(title=f"{ticker} daily — vung BULLISH la khi gia tren MA50",
                      xaxis_rangeslider_visible=False, height=480)
    # nhan "MM/YY" (co nam de khoi nham) moi ~30 ngay 1 nhan, an cuoi tuan
    _dti = dly.index[::30]
    fig.update_xaxes(
        tickmode="array", tickvals=_dti,
        ticktext=[_t.strftime("%m/%y") for _t in _dti],
        rangebreaks=[dict(bounds=["sat", "mon"])],
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    sig = ((dly["c"] > dly["ma50"]) & (vni["c"] > vni["ma50"])).fillna(False)
    pos = sig.shift(1).fillna(False)
    strat = (pos * dly["c"].pct_change() - pos.diff().abs() * COST / 2).dropna()
    bh = dly["c"].pct_change().dropna()
    eq_s, eq_b = (1 + strat).cumprod(), (1 + bh).cumprod()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=eq_s.index, y=eq_s, name="Chien luoc trend"))
    fig2.add_trace(go.Scatter(x=eq_b.index, y=eq_b, name=f"Mua-nam-giu {ticker}"))
    fig2.update_layout(title="Duong cong tai san (ty le, bat dau = 1)",
                       height=420)
    # dong bo nhan nhu tab gia: "MM/YY", an cuoi tuan
    _dti2 = eq_s.index[::30]
    fig2.update_xaxes(
        tickmode="array", tickvals=_dti2,
        ticktext=[_t.strftime("%m/%y") for _t in _dti2],
        rangebreaks=[dict(bounds=["sat", "mon"])],
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.caption(f"Chien luoc: {(eq_s.iloc[-1]-1):+.1%} | Mua-nam-giu: {(eq_b.iloc[-1]-1):+.1%} "
               f"| Thoi gian nam giu: {sig.mean():.0%}")

with tab3:
    recent = m15[m15.index >= (m15.index.max() - pd.Timedelta("14D"))]
    fig3 = go.Figure()
    fig3.add_trace(go.Candlestick(x=recent.index, open=recent["o"], high=recent["h"],
                                  low=recent["l"], close=recent["c"], name=f"{ticker} 15m"))
    fig3.update_layout(title=f"{ticker} 15m — 14 ngay gan nhat",
                       xaxis_rangeslider_visible=False, height=420)
    # an phien nghi (cuoi tuan / nghi trua 11:30-13:00 / qua dem)
    # nhan cho TUNG NEN 15p: "HH:MM", dau ngay kem "DD/MM" (chu nho, dung de vua)
    _tick_idx = recent.index
    _texts, _prev = [], None
    for _t in _tick_idx:
        _d = _t.date()
        if _d != _prev:
            _texts.append(_t.strftime("%d/%m<br>%H:%M"))
            _prev = _d
        else:
            _texts.append(_t.strftime("%H:%M"))
    fig3.update_xaxes(
        tickmode="array", tickvals=list(_tick_idx), ticktext=_texts,
        tickangle=-90, tickfont=dict(size=8),
        rangebreaks=[
            dict(bounds=["sat", "mon"]),
            dict(bounds=[11.5, 12.99], pattern="hour"),
            dict(bounds=[14.75, 9.2], pattern="hour"),
        ],
    )
    # duong chi gio: hover toi dau, ke dut net chieu xuong truc gio + sang truc gia
    fig3.update_xaxes(showspikes=True, spikemode="across+toaxis",
                      spikesnap="data", spikedash="dot", spikethickness=1)
    fig3.update_yaxes(showspikes=True, spikemode="across+toaxis",
                      spikesnap="data", spikedash="dot", spikethickness=1)
    st.plotly_chart(fig3, use_container_width=True)
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=recent.index, y=rsi_wilder(recent["c"], 50),
                              name="RSI(50)"))
    fig4.add_hline(y=53, line_dash="dash", line_color="red",
                   annotation_text="nguong momentum long")
    fig4.update_layout(title="RSI(50) khung 15m", height=400)
    fig4.update_xaxes(showspikes=True, spikemode="across+toaxis",
                      spikesnap="data", spikedash="dot", spikethickness=1)
    fig4.update_yaxes(showspikes=True, spikemode="across+toaxis",
                      spikesnap="data", spikedash="dot", spikethickness=1)
    st.plotly_chart(fig4, use_container_width=True)

with tab4:
    st.subheader("Phac thao trend tuong lai")
    st.caption("Ngoai suy toan hoc tu da hien tai + bien dao dong lich su. "
               "Day la KICH BAN tham khao, khong phai du bao gia.")
    cA, cB = st.columns(2)
    lookback = cA.slider("So ngay do trend", 20, 120, 60)
    horizon = cB.slider("So ngay phac thao toi", 5, 60, 20)

    with st.expander("Huong dan chinh thanh truot (tu kiem chung 16 cap thong so)"):
        st.markdown("""
- **Mac dinh 60/20** la can bang tot nhat cho ke hoach thang.
- **Thi truong bien dong manh, muon nhay hon:** keo ve **30/10**.
- **Nguyen tac:** so ngay phac khong qua **1/3** so ngay do (do 60 → phac toi da 20).
- **Khong phac qua 30 ngay** — sai so tren 30%, vung bien rong vo nghia.
- **So ngay do** gan nhu khong anh huong do chinh xac (do 20 hay 90 ngay chech nhau chi 2-3%):
  do dai thi muot, do ngan thi nhay — chon theo so thich.
- **Sai so trung binh thuc te:** phac 5 ngay ~8% | 10 ngay ~12% | 20 ngay ~21% | 30 ngay ~30%.
""")

    px = dly["c"].dropna().tail(lookback)
    x = np.arange(len(px))
    y = np.log(px.values)
    a, b = np.polyfit(x, y, 1)          # log-gia = a*x + b
    resid = y - (a * x + b)
    sigma = resid.std()
    # HIEU CHINH TRUNG THUC: sai so du bao thuc te gap ~3.4 lan sigma noi suy
    # (kiem chung 144 lan tren VIX: gia roi vao ±1σ hieu chinh 79%, ±2σ 93%)
    emp = sigma * 3.4 * np.sqrt(horizon / 20)
    slope_day = (np.exp(a) - 1) * 100

    xf = np.arange(len(px), len(px) + horizon)
    fut_idx = pd.bdate_range(px.index[-1] + pd.Timedelta(days=1),
                             periods=horizon, tz="Asia/Ho_Chi_Minh")
    # anchor projection at last actual price, extend with measured slope
    log_last = np.log(px.iloc[-1])
    yf = log_last + a * (xf - (len(px) - 1))
    proj = np.exp(yf)
    b1u, b1d = np.exp(yf + emp), np.exp(yf - emp)
    b2u, b2d = np.exp(yf + 2 * emp), np.exp(yf - 2 * emp)

    trend_txt = "TANG" if a > 0 else "GIAM"
    st.info(f"Da {lookback} ngay: **{trend_txt}** {abs(slope_day):.2f}%/ngay | "
            f"Gia hien tai {px.iloc[-1]:.2f} | Du kien {horizon} ngay toi: "
            f"~{proj[-1]:.2f} (bien ±1σ: {b1d[-1]:.2f}–{b1u[-1]:.2f})")

    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(x=px.index, y=px.values, name="Gia qua khu",
                              line=dict(color="black", width=1.5)))
    fig5.add_trace(go.Scatter(x=fut_idx, y=proj, name="Ngoai suy trend",
                              line=dict(color="blue", dash="dash", width=2)))
    for uu, dd, nm, col in [(b2u, b2d, "Bien ±2σ (95%)", "rgba(0,0,255,0.06)"),
                            (b1u, b1d, "Bien ±1σ (68%)", "rgba(0,0,255,0.12)")]:
        fig5.add_trace(go.Scatter(
            x=list(fut_idx) + list(fut_idx[::-1]),
            y=list(uu) + list(dd[::-1]), fill="toself",
            fillcolor=col, line=dict(width=0), name=nm))
    hi, lo = px.max(), px.min()
    fig5.add_hline(y=hi, line_dash="dot", line_color="red",
                   annotation_text=f"Khang cu {hi:.2f}")
    fig5.add_hline(y=lo, line_dash="dot", line_color="green",
                   annotation_text=f"Ho tro {lo:.2f}")
    fig5.update_layout(title=f"Kich ban {horizon} ngay toi (du tren {lookback} ngay qua khu)",
                       height=480)
    # nhan theo format YYYY-MM-DD, moi ngay 1 nhan (chu nho, dung)
    _allx = list(px.index) + list(fut_idx)
    fig5.update_xaxes(
        tickmode="array", tickvals=_allx,
        ticktext=[_t.strftime("%Y-%m-%d") for _t in _allx],
        tickangle=-90, tickfont=dict(size=8),
        rangebreaks=[dict(bounds=["sat", "mon"])],
    )
    st.plotly_chart(fig5, use_container_width=True)
    st.caption("Doc bieu do: duong dut net xanh la huong di neu da hien tai giu nguyen; "
               "vung xanh la bien dao dong HIEU CHINH theo sai so du bao thuc te "
               "(he so hieu chinh do tren VIX; moi ma co bien dong khac nhau). "
               "Vung rong la binh thuong — du bao gia co phieu von kem chinh xac.")

st.divider()
st.caption("Du lieu: Vietcap public API | Mo hinh trung han backtest 800 ngay tren VIX | "
           "Khong phai khuyen nghi dau tu. Xem BAO_CAO_MO_HINH.md truoc khi dung.")
