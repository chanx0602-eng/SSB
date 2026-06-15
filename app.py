import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
from pykrx import stock as krx

API_KEY = "de924ae6c9703a84f1692ac05189e7a9a8796f713f4b08e4342aee0e9d6edff7"
BASE_URL = "http://apis.data.go.kr/1160100/service/GetCMStckLnbInfoService"

STOCKS = {
    "005930": "삼성전자", "000660": "SK하이닉스", "009150": "삼성전기",
    "066570": "LG전자", "000150": "두산", "011070": "LG이노텍",
    "007660": "이수페타시스", "000990": "DB하이텍", "353200": "대덕전자",
    "103590": "일진전기", "489790": "한화비젼", "014680": "한솔케미칼",
    "007810": "코스모화학", "036930": "주성엔지니어링", "058470": "리노공업",
    "039030": "이오테크닉스", "240810": "원익IPS", "095340": "ISC",
    "403870": "HPSP", "222800": "심텍", "010170": "대한전선",
    "080220": "제주반도체", "131970": "두산테스나", "067310": "하나마이크론",
    "319660": "피에스케이홀딩스", "064760": "티씨케이", "357780": "솔브레인",
    "005290": "동진쎄미켐", "043260": "성호전자", "084370": "유진테크",
    "031980": "피에스케이", "131290": "티에스이", "218410": "RFHIC",
    "095610": "테스", "089030": "테크윙", "140860": "파크시스템스",
    "101490": "에스앤에스텍", "183300": "코미코", "420770": "기가비스",
    "166090": "하나머티리얼즈", "036540": "에스에프에이", "490470": "한화비전",
    "388210": "에이피에이치", "213420": "덕산네오룩스", "083450": "GST",
    "056190": "에스에프씨", "089970": "브이엠", "373220": "LG에너지솔루션",
    "006400": "삼성SDI", "247540": "에코프로비엠"
}

st.title("📊 공매도 · 대차잔고 대시보드")

today = datetime.today()
last_monday = today - timedelta(days=today.weekday() + 7)
last_friday = last_monday + timedelta(days=4)

col1, col2 = st.columns(2)
with col1:
    start = st.date_input("시작일", value=last_monday)
with col2:
    end = st.date_input("종료일", value=last_friday)

tab1, tab2 = st.tabs(["📉 대차잔고", "🔻 공매도"])

# ── TAB 1: 대차잔고 (기존 공공API) ─────────────────────────────────────────
with tab1:
    if st.button("조회", key="btn1"):
        all_data = {}
        progress = st.progress(0)
        status = st.empty()
        for i, (code, name) in enumerate(STOCKS.items()):
            status.text(f"{name} 불러오는 중... ({i+1}/{len(STOCKS)})")
            try:
                url = (
                    f"{BASE_URL}/getStckLnbDetail"
                    f"?serviceKey={API_KEY}"
                    f"&resultType=json"
                    f"&numOfRows=100"
                    f"&pageNo=1"
                    f"&beginBasDt={start.strftime('%Y%m%d')}"
                    f"&endBasDt={end.strftime('%Y%m%d')}"
                    f"&stckItmsCd={code}"
                )
                res = requests.get(url)
                data = res.json()
                items = data["response"]["body"]["items"]["item"]
                if items:
                    df = pd.DataFrame(items)
                    df["날짜"] = pd.to_datetime(df["basDt"])
                    df["대차잔고금액"] = pd.to_numeric(df["balnStckAmt"], errors="coerce") / 1_000_000_000
                    all_data[name] = df.set_index("날짜")["대차잔고금액"]
            except:
                pass
            progress.progress((i + 1) / len(STOCKS))

        status.text("완료!")
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

# ── TAB 2: 공매도 (pykrx — 쿠키 불필요) ────────────────────────────────────
with tab2:
    if st.button("조회", key="btn2"):
        all_val = {}
        progress = st.progress(0)
        status = st.empty()
        start_str = start.strftime("%Y%m%d")
        end_str = end.strftime("%Y%m%d")

        for i, (code, name) in enumerate(STOCKS.items()):
            status.text(f"{name} 공매도 불러오는 중... ({i+1}/{len(STOCKS)})")
            try:
                df = krx.get_shorting_volume_by_date(start_str, end_str, code)
                # 거래대금 컬럼
                df2 = krx.get_shorting_value_by_date(start_str, end_str, code)
                if not df2.empty and "공매도" in df2.columns:
                    series = df2["공매도"] / 1_000_000_000
                    series.index = pd.to_datetime(series.index)
                    all_val[name] = series
            except:
                pass
            progress.progress((i + 1) / len(STOCKS))

        status.text("완료!")
        if all_val:
            chart_val = pd.DataFrame(all_val)
            st.subheader("공매도 거래대금 (단위: 십억원)")
            st.dataframe(chart_val.style.format("{:,.2f}"))
            st.subheader("종목별 공매도 거래대금 (단위: 십억원)")
            cols = st.columns(2)
            for i, (name, series) in enumerate(all_val.items()):
                with cols[i % 2]:
                    st.markdown(f"**{name}**")
                    st.bar_chart(series)
        else:
            st.error("공매도 데이터를 가져오지 못했어요. 날짜 범위를 확인해주세요.")
