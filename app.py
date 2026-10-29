import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (와이드 모드)
st.set_page_config(
    page_title="본사 문직 제품 수주 및 출고 관리 시스템", layout="wide"
)

st.title("📦 본사 문직 제품 수주 및 출고 관리 시스템")
st.markdown("구글 스프레드시트와 실시간 연동된 SCM 대시보드입니다.")

# 새로 발급받은 구글 앱스 스크립트 웹 앱 URL 적용
web_app_url = (
    "https://script.google.com/macros/s/AKfycbzOEI1bBuSYXtf5MrbnmQ4J4pQwdJy7yvomVRYAdvjdgG2nujsMTyTP--DWkb0oFG5x/exec"
)

# 데이터 로딩 상태 표시
with st.spinner("구글 시트에서 데이터를 불러오는 중입니다..."):
  try:
    # 웹 앱 주소로 데이터 요청
    response = requests.get(web_app_url)
    data = response.json()

    # 데이터가 비어있는지 확인
    if data:
      # 판다스 데이터프레임으로 변환
      df = pd.DataFrame(data)

      st.success("데이터를 성공적으로 불러왔습니다!")

      # 검색 기능 추가 (품명, 출하처 등 검색)
      search_keyword = st.text_input(
          "🔍 검색어 입력 (품명, 출하처 등 검색)", ""
      )

      if search_keyword:
        # 데이터프레임 내에서 검색어가 포함된 행만 필터링
        filtered_df = df[
            df.astype(str)
            .apply(lambda row: row.str.contains(search_keyword, case=False))
