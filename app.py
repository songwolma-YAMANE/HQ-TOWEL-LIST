import pandas as pd
import streamlit as st

st.sidebar.title("데이터 소스 설정")

# 1. session_state에 데이터프레임이 아직 없다면 초기화
if "df" not in st.session_state:
  st.session_state.df = None

# 2. 파일 업로더 생성
uploaded_file = st.sidebar.file_uploader(
    "수주/출고 데이터 파일 업로드 (Excel / CSV)", type=["xlsx", "csv"]
)

# 3. 새로운 파일이 업로드되면 session_state에 데이터프레임 저장
if uploaded_file is not None:
  try:
    if uploaded_file.name.endswith(".csv"):
      # 필요에 따라 header=1 등 행 번호 지정
      st.session_state.df = pd.read_csv(uploaded_file, header=1)
    else:
      st.session_state.df = pd.read_excel(uploaded_file, header=1)
    st.sidebar.success("파일 업로드 및 로드 완료!")
  except Exception as e:
    st.sidebar.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

# 4. 저장된 데이터가 있는 경우 대시보드 표시
if st.session_state.df is not None:
  st.success("데이터를 성공적으로 불러왔습니다!")
  st.dataframe(st.session_state.df)

  # [선택사항] 업로드된 데이터를 굳이 지우고 다시 올리고 싶을 때 쓰는 초기화 버튼
  if st.sidebar.button("데이터 초기화"):
    st.session_state.df = None
    st.rerun()
else:
  st.info(
      "👈 사이드바에서 수주 및 출고 관리 데이터 파일(.xlsx 또는 .csv)을"
      " 업로드해 주세요."
  )
