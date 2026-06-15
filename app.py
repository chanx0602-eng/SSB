import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

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

def get_isin(code):
    return f"KR7{code}000"

st.title("📊 공매도 · 대차잔고 대시보드")

today = datetime.today()
last_monday = today - timedelta(days=today.weekday() + 7)
last_friday = last_monday + timedelta(days=4)

col1, col2 = st.columns(2)
with col1:
    start = st.date_input("시작일", value=last_monday)
with col2:
    end = st.date_input("종료일", value=last_friday)

# ── KRX 쿠키 설정 ──────────────────────────────────────────────────────────
with st.expander("⚙️ KRX 쿠키 설정 (공매도 탭 필요)", expanded=False):
    st.markdown(
        "1. [data.krx.co.kr](https://data.krx.co.kr) 로그인\n"
        "2. F12 → Network → 아무 요청 클릭 → Request Headers의 **Cookie** 값 복사\n"
        "3. 아래 붙여넣기 후 저장"
    )
    krx_cookie_input = st.text_area(
        "KRX Cookie",
        value=st.session_state.get("krx_cookie", ""),
        height=80,
        placeholder="JSESSIONID=... 형태로 붙여넣기",
    )
    if st.button("쿠키 저장"):
        st.session_state["krx_cookie"] = krx_cookie_input
        st.success("저장됐어요!")

def get_krx_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://data.krx.co.kr/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": st.session_state.get("krx_cookie", ""),
    }

tab1, tab2 = st.tabs(["📉 대차잔고", "🔻 공매도"])

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

with tab2:
    if st.button("조회", key="btn2"):
        if not st.session_state.get("krx_cookie", ""):
            st.warning("⚠️ 위 '⚙️ KRX 쿠키 설정'에서 쿠키를 먼저 입력해주세요.")
        else:
            all_val = {}
            progress = st.progress(0)
            status = st.empty()
            for i, (code, name) in enumerate(STOCKS.items()):
                status.text(f"{name} 공매도 불러오는 중... ({i+1}/{len(STOCKS)})")
                try:
                    res = requests.post(
                        "https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd",
                        data={
                            "bld": "dbms/MDC/STAT/srt/MDCSTAT30001",
                            "locale": "ko_KR",
                            "isuCd": get_isin(code),
                            "strtDd": start.strftime("%Y%m%d"),
                            "endDd": end.strftime("%Y%m%d"),
                            "share": "1",
                            "money": "1",
                            "csvxls_isNo": "false"
                        },
                        headers=get_krx_headers(),
                        timeout=10
                    )
                    data = res.json()
                    if "OutBlock_1" in data and data["OutBlock_1"]:
                        df = pd.DataFrame(data["OutBlock_1"])
                        df["날짜"] = pd.to_datetime(df["TRD_DD"])
                        df = df.set_index("날짜")
                        all_val[name] = (
                            df["CVSRTSELL_TRDVAL"]
                            .astype(str).str.replace(",", "")
                            .apply(pd.to_numeric, errors="coerce")
                            / 1_000_000_000
                        )
                except:
                    pass
                progress.progress((i + 1) / len(STOCKS))

            status.text("완료!")
            if all_val:
                chart_val = pd.DataFrame(all_val)
                st.subheader("상세 데이터 (단위: 십억원)")
                st.dataframe(chart_val.style.format("{:,.2f}"))
                st.subheader("종목별 공매도 거래대금 (단위: 십억원)")
                cols = st.columns(2)
                for i, (name, series) in enumerate(all_val.items()):
                    with cols[i % 2]:
                        st.markdown(f"**{name}**")
                        st.bar_chart(series)
            else:
                st.error("데이터를 가져오지 못했어요. 쿠키가 만료됐을 수 있어요. 위 설정에서 쿠키를 다시 입력해주세요.")
