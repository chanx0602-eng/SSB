import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

API_KEY = "de924ae6c9703a84f1692ac05189e7a9a8796f713f4b08e4342aee0e9d6edff7"
BASE_URL = "http://apis.data.go.kr/1160100/service/GetCMStckLnbInfoService/getStckLnbDetail"

STOCKS = {
    "005930": "삼성전자", "000660": "SK하이닉스", "402340": "SK스퀘어", "009150": "삼성전기",
    "066570": "LG전자", "000150": "두산", "011070": "LG이노텍",
    "007660": "이수페타시스", "000990": "DB하이텍", "353200": "대덕전자",
    "103590": "일진전기", "489790": "한화비전", "014680": "한솔케미칼",
    "007810": "코리아써키트", "036930": "주성엔지니어링", "058470": "리노공업",
    "039030": "이오테크닉스", "240810": "원익IPS", "095340": "ISC",
    "403870": "HPSP", "222800": "심텍", "010170": "대한전선",
    "080220": "제주반도체", "131970": "두산테스나", "067310": "하나마이크론",
    "319660": "피에스케이홀딩스", "064760": "티씨케이", "357780": "솔브레인",
    "005290": "동진쎄미켐", "043260": "성호전자", "084370": "유진테크",
    "031980": "피에스케이", "131290": "티에스이", "218410": "RFHIC",
    "095610": "테스", "089030": "테크윙", "140860": "파크시스템스",
    "101490": "에스앤에스텍", "183300": "코미코", "420770": "기가비스",
    "166090": "하나머티리얼즈", "036540": "에스에프에이",
    "388210": "에이피에이치", "213420": "덕산네오룩스", "083450": "GST",
    "056190": "에스에프씨", "089970": "브이엠", "373220": "LG에너지솔루션",
    "006400": "삼성SDI", "247540": "에코프로비엠"
}

def fetch_data(code, start, end):
    url = (
        f"{BASE_URL}?serviceKey={API_KEY}"
        f"&resultType=json&numOfRows=100&pageNo=1"
        f"&beginBasDt={start}&endBasDt={end}&stckItmsCd={code}"
    )
    res = requests.get(url, timeout=10)
    data = res.json()
    items = data["response"]["body"]["items"]["item"]
    if not items:
        return pd.DataFrame()
    df = pd.DataFrame(items if isinstance(items, list) else [items])
    df["날짜"] = pd.to_datetime(df["basDt"])
    df = df.set_index("날짜").sort_index()
    return df

def run_query(col_name, divide_by_billion=False):
    all_data = {}
    progress = st.progress(0)
    status = st.empty()
    for i, (code, name) in enumerate(STOCKS.items()):
        status.text(f"{name} 불러오는 중... ({i+1}/{len(STOCKS)})")
        try:
            df = fetch_data(code, start_str, end_str)
            if not df.empty and col_name in df.columns:
                series = pd.to_numeric(df[col_name], errors="coerce")
                if divide_by_billion:
                    series = series / 1_000_000_000
                all_data[name] = series
        except:
            pass
        progress.progress((i + 1) / len(STOCKS))
    status.text("완료!")
    return all_data

# ── UI ───────────────────────────────────────────────────
st.title("📊 공매도 · 대차잔고 대시보드")

today = datetime.today()
last_monday = today - timedelta(days=today.weekday() + 7)
last_friday = last_monday + timedelta(days=4)

col1, col2 = st.columns(2)
with col1:
    start = st.date_input("시작일", value=last_monday)
with col2:
    end = st.date_input("종료일", value=last_friday)

start_str = start.strftime("%Y%m%d")
end_str = end.strftime("%Y%m%d")

tab1, tab2 = st.tabs(["📉 대차잔고", "🔻 공매도 (대차체결 기준)"])

# ── 대차잔고 탭 ──────────────────────────────────────────
with tab1:
    if st.button("조회", key="btn1"):
        all_data = run_query("balnStckAmt", divide_by_billion=True)
        if all_data:
            chart_data = pd.DataFrame(all_data)
            st.subheader("상세 데이터 (단위: 십억원)")
            st.dataframe(chart_data.style.format("{:,.2f}"))
            st.subheader("종목별 대차잔고 금액 (단위: 십억원)")
            cols = st.columns(2)
            for i, (name, series) in enumerate(all_data.items()):
                with cols[i % 2]:
                    st.markdown(f"**{name}**")
                    st.bar_chart(series)
        else:
            st.warning("데이터가 없어요.")

# ── 공매도 탭 (근사치) ───────────────────────────────────
with tab2:
    st.caption("※ KRX 공매도 거래대금 직접 제공처가 차단되어, 공공데이터포털의 대차 체결주식수를 근사치로 표시합니다.")
    if st.button("조회", key="btn2"):
        all_data = run_query("cclStckCnt", divide_by_billion=False)
        if all_data:
            chart_data = pd.DataFrame(all_data)
            st.subheader("상세 데이터 (단위: 주)")
            st.dataframe(chart_data.style.format("{:,.0f}"))
            st.subheader("종목별 대차 체결주식수 (단위: 주)")
            cols = st.columns(2)
            for i, (name, series) in enumerate(all_data.items()):
                with cols[i % 2]:
                    st.markdown(f"**{name}**")
                    st.line_chart(series)
        else:
            st.warning("데이터가 없어요.")
