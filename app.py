import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="HQ Textile Order Management", layout="wide")

st.markdown(
    """
    <style>
    .main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-header">📦 본사 문직 제품 수주 및 출고 관리 시스템</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">실시간 SCM 대시보드 (구글 스프레드시트 연동 버전)</div>',
    unsafe_allow_html=True,
)

DEFAULT_GSHEET_URL = "https://docs.google.com/spreadsheets/d/13Lp9gA3p8a_WstCQA9AMrfzM8YTtqUpBV8Ryxzsjg/export?format=csv&gid=351025401"

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ 데이터 소스 설정")
sheet_url = st.sidebar.text_input(
    "구글 시트 CSV 내보내기 링크", value=DEFAULT_GSHEET_URL
)

if st.sidebar.button("🔄 데이터 새로고침"):
  st.cache_data.clear()
  st.sidebar.success("캐시가 초기화되었습니다!")
  st.rerun()


@st.cache_data(ttl=60)
def load_google_sheet(url):
  try:
    # requests로 직접 데이터를 긁어와서 인코딩 및 파싱 에러 방지
    response = requests.get(url)
    response.raise_for_status()
    from io import StringIO

    df = pd.read_csv(StringIO(response.text))
    return df
  except Exception as e:
    try:
      # 만약 헤더가 두 번째 줄에 있다면
      from io import StringIO

      df = pd.read_csv(StringIO(response.text), header=1)
      return df
    except Exception as e2:
      return None


if not sheet_url:
  st.info("👋 **[안내]** 사이드바에 구글 스프레드시트 링크를 입력해 주세요.")
  st.stop()

df = load_google_sheet(sheet_url)

if df is None or df.empty:
  st.error(
      "🚨 구글 스프레드시트 데이터를 불러오는 데 실패했습니다. 아래 사항을"
      " 확인해 주세요."
  )
  st.markdown("""
    > 💡 **체크포인트:**
    > 1. 구글 스프레드시트 상단 우측 **[공유]** ➔ 일반 접근 권한 **[링크가 있는 모든 사용자] (뷰어)**로 설정되어 있는지 확인
    > 2. 시트가 비어있지 않고 실제 데이터가 입력되어 있는지 확인
    """)
  st.stop()

try:
  # 데이터 정제
  df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
  df.columns = df.columns.astype(str).str.strip()

  for col in df.columns:
    if any(k in col for k in ["납기", "일자", "날짜", "수령"]):
      df[col] = (
          pd.to_datetime(df[col], errors="coerce")
          .dt.strftime("%Y-%m-%d")
          .fillna(df[col].astype(str))
      )
      df[col] = df[col].replace(["NaT", "nan", "NaT 00:00:00"], "")

  search_query = st.text_input("🔍 검색 (출하처, 제품명, 대리점 등 입력)", "")
  filtered_df = df.copy()
  if search_query:
    cond = pd.Series(False, index=filtered_df.index)
    for col in filtered_df.columns:
      cond = cond | filtered_df[col].astype(str).str.contains(
          search_query, na=False, case=False
      )
    filtered_df = filtered_df[cond]

  st.data_editor(filtered_df, use_container_width=True, height=700)

except Exception as e:
  st.error(f"데이터 처리 중 오류 발생: {e}")
