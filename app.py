import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

API_KEY = "de924ae6c9703a84f1692ac05189e7a9a8796f713f4b08e4342aee0e9d6edff7"
LNB_URL = "http://apis.data.go.kr/1160100/service/GetCMStckLnbInfoService/getStckLnbDetail"

# 종목코드: (종목명, ISIN코드)
STOCKS = {
    "005930": ("삼성전자", "KR7005930003"),
    "000660": ("SK하이닉스", "KR7000660001"),
    "009150": ("삼성전기", "KR7009150004"),
    "066570": ("LG전자", "KR7066570003"),
    "000150": ("두산", "KR7000150009"),
    "011070": ("LG이노텍", "KR7011070000"),
    "007660": ("이수페타시스", "KR7007660006"),
    "000990": ("DB하이텍", "KR7000990001"),
    "353200": ("대덕전자", "KR7353200009"),
    "103590": ("일진전기", "KR7103590004"),
    "489790": ("한화비전", "KR7489790000"),
    "014680": ("한솔케미칼", "KR7014680005"),
    "007810": ("코리아써키트", "KR7007810009"),
    "036930": ("주성엔지니어링", "KR7036930006"),
    "058470": ("리노공업", "KR7058470001"),
    "039030": ("이오테크닉스", "KR7039030004"),
    "240810": ("원익IPS", "KR7240810002"),
    "095340": ("ISC", "KR7095340009"),
    "403870": ("HPSP", "KR7403870003"),
    "222800": ("심텍", "KR7222800007"),
    "010170": ("대한전선", "KR7010170002"),
    "080220": ("제주반도체", "KR7080220005"),
    "131970": ("두산테스나", "KR7131970005"),
    "067310": ("하나마이크론", "KR7067310002"),
    "319660": ("피에스케이홀딩스", "KR7319660006"),
    "064760": ("티씨케이", "KR7064760003"),
    "357780": ("솔브레인", "KR7357780002"),
    "005290": ("동진쎄미켐", "KR7005290008"),
    "043260": ("성호전자", "KR7043260009"),
    "084370": ("유진테크", "KR7084370003"),
    "031980": ("피에스케이", "KR7031980000"),
    "131290": ("티에스이", "KR7131290007"),
    "218410": ("RFHIC", "KR7218410006"),
    "095610": ("테스", "KR7095610006"),
    "089030": ("테크윙", "KR7089030001"),
    "140860": ("파크시스템스", "KR7140860009"),
    "101490": ("에스앤에스텍", "KR7101490008"),
    "183300": ("코미코", "KR7183300007"),
    "420770": ("기가비스", "KR7420770005"),
    "166090": ("하나머티리얼즈", "KR7166090007"),
    "036540": ("에스에프에이", "KR7036540003"),
    "388210": ("에이피에이치", "KR7388210000"),
    "213420": ("덕산네오룩스", "KR7213420006"),
    "083450": ("GST", "KR7083450003"),
    "056190": ("에스에프씨", "KR7056190009"),
    "089970": ("브이엠", "KR7089970005"),
    "373220": ("LG에너지솔루션", "KR7373220003"),
    "006400": ("삼성SDI", "KR7006400006"),
    "247540": ("에코프로비엠", "KR7247540008"),
}

# ── Selenium으로 쿠키 자동 발급 ─────────────────────────
def get_fresh_cookie():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    try:
        driver.get("https://data.krx.co.kr/comm/srt/srtLoader/index.cmd?screenId=MDCSTAT300&isuCd=005930")
        time.sleep(3)
        selenium_cookies = driver.get_cookies()
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in selenium_cookies])
        return cookie_str
    finally:
        driver.quit()

def get_krx_headers(cookie_str):
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://data.krx.co.kr",
        "Referer": "https://data.krx.co.kr/comm/srt/srtLoader/index.cmd?screenId=MDCSTAT300&isuCd=005930",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": cookie_str,
    }

def fetch_lend(code, start, end):
    url = (
        f"{LNB_URL}?serviceKey={API_KEY}"
        f"&resultType=json&numOfRows=100&pageNo=1"
        f"&beginBasDt={start}&endBasDt={end}&stckItmsCd={code}"
    )
    res = requests.get(url, timeout=10)
    data = res.json()
    items = data["response"]["body"]["items"]["item"]
    if not items:
        return pd.Series(dtype=float)
    df = pd.DataFrame(items if isinstance(items, list) else [items])
    df["날짜"] = pd.to_datetime(df["basDt"])
    df = df.set_index("날짜").sort_index()
    return pd.to_numeric(df["balnStckAmt"], errors="coerce") / 1_000_000_000

def fetch_short(isu_cd, start, end, cookie_str):
    res = requests.post(
        "https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd",
        data={
            "bld": "dbms/MDC_OUT/STAT/srt/MDCSTAT30001_OUT",
            "locale": "ko_KR",
            "isuCd": isu_cd,
            "isuCd2": "",
            "strtDd": start,
            "endDd": end,
            "share": "1",
            "money": "1",
            "csvxls_isNo": "false"
        },
        headers=get_krx_headers(cookie_str),
        timeout=10
    )
    data = res.json()
    if "OutBlock_1" not in data or not data["OutBlock_1"]:
        return pd.Series(dtype=float)
    df = pd.DataFrame(data["OutBlock_1"])
    df["날짜"] = pd.to_datetime(df["TRD_DD"], errors="coerce")
    val_col = "CVSRTSELL_TRDVAL" if "CVSRTSELL_TRDVAL" in df.columns else None
    if val_col is None:
        for c in df.columns:
            if "TRDVAL" in c:
                val_col = c
                break
    df["값"] = df[val_col].astype(str).str.replace(",", "").astype(float) / 1_000_000_000
    return df.set_index("날짜")["값"].sort_index()

# ── UI ───────────────────────────────────────────────────
st.title("📊 공매도 · 대차잔고 대시보드")

if "krx_cookie" not in st.session_state:
    st.session_state.krx_cookie = None

st.sidebar.title("⚙️ 설정")
if st.sidebar.button("🔄 KRX 쿠키 갱신 (Chrome 실행)"):
    with st.spinner("Chrome으로 KRX 접속 중... (10~20초 소요)"):
        try:
            st.session_state.krx_cookie = get_fresh_cookie()
            st.sidebar.success("✅ 쿠키 갱신 완료!")
        except Exception as e:
            st.sidebar.error(f"갱신 실패: {e}")

if st.session_state.krx_cookie:
    st.sidebar.info("🟢 쿠키 보유 중")
else:
    st.sidebar.warning("🔴 쿠키 없음 — 공매도 조회 전 갱신 필요")

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

tab1, tab2 = st.tabs(["📉 대차잔고", "🔻 공매도"])

# ── 대차잔고 ─────────────────────────────────────────────
with tab1:
    if st.button("조회", key="btn1"):
        all_data = {}
        progress = st.progress(0)
        status = st.empty()
        for i, (code, (name, isu)) in enumerate(STOCKS.items()):
            status.text(f"{name} 대차잔고 조회 중... ({i+1}/{len(STOCKS)})")
            try:
                s = fetch_lend(code, start_str, end_str)
                if not s.empty:
                    all_data[name] = s
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
        else:
            st.warning("데이터가 없어요.")

# ── 공매도 ───────────────────────────────────────────────
with tab2:
    if not st.session_state.krx_cookie:
        st.warning("⚠️ 먼저 왼쪽 사이드바에서 '쿠키 갱신' 버튼을 눌러주세요.")
    elif st.button("조회", key="btn2"):
        all_data = {}
        progress = st.progress(0)
        status = st.empty()
        for i, (code, (name, isu)) in enumerate(STOCKS.items()):
            status.text(f"{name} 공매도 조회 중... ({i+1}/{len(STOCKS)})")
            try:
                s = fetch_short(isu, start_str, end_str, st.session_state.krx_cookie)
                if not s.empty:
                    all_data[name] = s
            except:
                pass
            progress.progress((i + 1) / len(STOCKS))
        status.text("완료!")
        if all_data:
            chart_data = pd.DataFrame(all_data)
            st.subheader("상세 데이터 (단위: 십억원)")
            st.dataframe(chart_data.style.format("{:,.4f}"))
            st.subheader("종목별 공매도 거래대금 (단위: 십억원)")
            cols = st.columns(2)
            for i, (name, series) in enumerate(all_data.items()):
                with cols[i % 2]:
                    st.markdown(f"**{name}**")
                    st.line_chart(series)
        else:
            st.warning("데이터를 가져오지 못했어요. 쿠키를 다시 갱신해보세요.")
