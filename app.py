import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (와이드 모드)
st.set_page_config(
    page_title="본사 문직 제품 수주 및 출고 관리 시스템", layout="wide"
)

st.title("📦 본사 문직 제품 수주 및 출고 관리 시스템")
st.markdown(
    "구글 스프레드시트와 실시간 연동된 SCM 대시보드입니다. (캐싱, 새로고침,"
    " 통화포맷 적용)"
)

# 💡 구글 앱스 스크립트 웹 앱 URL을 아래에 정확히 입력해 주세요.
web_app_url = (
    "https://script.google.com/macros/s/AKfycby_4c8lsEFsWt66f8gu9d6q0z1dPUNJ1aLCHF7pz6M5RbjpNeykU2vbXDJZZYLoKKDL/exec"
)


# 캐시를 적용하여 데이터를 불러오는 함수 (ttl=600: 10분마다 자동 갱신)
@st.cache_data(ttl=600, show_spinner=False)
def load_data(url):
  response = requests.get(url)
  return response.json()


# 상단 우측에 [데이터 새로고침] 버튼 배치
col1, col2 = st.columns([6, 1])
with col2:
  if st.button("🔄 새로고침", use_container_width=True):
    load_data.clear()
    st.success("캐시가 초기화되었습니다!")
    st.rerun()

# 데이터 로딩 상태 표시
with st.spinner("구글 시트에서 데이터를 불러오는 중입니다..."):
  try:
    data = load_data(web_app_url)

    if data and len(data) > 0:
      df = pd.DataFrame(data)

      # 단가(FOB)와 총액(AMOUNT) 컬럼에 $ 및 천단위 콤마 포맷 적용
      for col in df.columns:
        if "단가" in col or "총액" in col or "AMOUNT" in col or "FOB" in col:
          df[col] = pd.to_numeric(
              df[col]
              .astype(str)
              .str.replace("$", "", regex=False)
              .str.replace(",", "", regex=False)
              .str.strip(),
              errors="coerce",
          )
          df[col] = df[col].apply(
              lambda x: f"$ {x:,.2f}" if pd.notnull(x) and x > 0 else ""
          )

      st.success(
          f"데이터를 성공적으로 불러왔습니다! (총 {len(df)}행 데이터 로드됨)"
      )

      # 검색 기능 추가
      search_keyword = st.text_input(
          "🔍 검색어 입력 (대리점, 품명, 출하처 등 검색)", ""
      )

      if search_keyword:
        mask = (
            df.astype(str)
            .apply(lambda row: row.str.contains(search_keyword, case=False))
            .any(axis=1)
        )
        filtered_df = df[mask]
        st.dataframe(filtered_df, use_container_width=True, height=600)
        st.info(f"검색 결과: 총 {len(filtered_df)}건")
      else:
        # 전체 데이터 표 출력 (발주서 수령일 기준 최신순 정렬 상태)
        st.dataframe(df, use_container_width=True, height=600)

    else:
      st.warning("가져온 데이터가 비어있습니다. 시트 내용을 확인해 주세요.")

  except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
