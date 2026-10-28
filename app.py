import pandas as pd
import streamlit as st

st.set_page_config(page_title="HQ Textile Order Management", layout="wide")

st.markdown("""
    <style>
    .main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📦 본사 문직 제품 수주 및 출고 관리 시스템</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">실시간 SCM 대시보드 (구글 스프레드시트 연동 버전)</div>', unsafe_allow_html=True)

# 구글 스프레드시트 CSV 내보내기 링크 설정
# (구글 시트 [파일] -> [공유] -> [웹에 게시] 또는 공개 링크의 CSV 다운로드 주소를 여기에 입력하세요)
DEFAULT_GSHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/export?format=csv"

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ 데이터 소스 설정")
sheet_url = st.sidebar.text_input("구글 시트 CSV 내보내기 링크", value=DEFAULT_GSHEET_URL)

# 새로고침 버튼
if st.sidebar.button("🔄 데이터 새로고침"):
    st.cache_data.clear()
    st.sidebar.success("캐시가 초기화되었습니다!")
    st.rerun()

# 데이터 로드 함수 (캐싱 적용)
@st.cache_data(ttl=600)
def load_data(url):
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        return None

if not sheet_url or "YOUR_SPREADSHEET_ID" in sheet_url:
    st.info("👋 **[안내]** 사이드바에 사용하실 **구글 스프레드시트 CSV 내보내기 링크**를 입력해 주세요!")
    st.stop()

# 데이터 불러오기
df = load_data(sheet_url)

if df is None:
    st.error("🚨 구글 스프레드시트 데이터를 불러오는 데 실패했습니다. 링크 주소나 공유 권한(링크가 있는 모든 사용자 보기 가능)을 확인해 주세요.")
    st.stop()

try:
    # 컬럼 공백 다듬기
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.columns = df.columns.astype(str).str.strip()

    # 날짜 형식 다듬기
    for col in df.columns:
        if any(k in col for k in ['납기', '일자', '날짜', '수령']):
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d').fillna(df[col].astype(str))
            df[col] = df[col].replace(['NaT', 'nan', 'NaT 00:00:00'], '')

    # 검색 기능
    search_query = st.text_input("🔍 검색 (출하처, 제품명, 대리점 등 입력)", "")
    filtered_df = df.copy()
    if search_query:
        cond = pd.Series(False, index=filtered_df.index)
        for col in filtered_df.columns:
            cond = cond | filtered_df[col].astype(str).str.contains(search_query, na=False, case=False)
        filtered_df = filtered_df[cond]

    # 스프레드시트 원본 형태 그대로 출력
    st.data_editor(filtered_df, use_container_width=True, height=700)

except Exception as e:
    st.error(f"데이터 처리 중 오류 발생: {e}")
