import pandas as pd
import streamlit as st

st.sidebar.title("데이터 소스 설정")
# 파일 업로드 위젯 추가 (Excel 및 CSV 지원)
uploaded_file = st.sidebar.file_uploader(
    "수주/출고 데이터 파일 업로드 (Excel / CSV)", type=["xlsx", "csv"]
)

if uploaded_file is not None:
  # 파일 형식에 따라 판다스로 읽기
  if uploaded_file.name.endswith(".csv"):
    df = pd.read_csv(uploaded_file)
  else:
    df = pd.read_excel(uploaded_file)

  st.success("데이터를 성공적으로 불러왔습니다!")
  # 이후 대시보드 시각화 및 데이터 테이블 표시 코드 작성
  st.dataframe(df)
else:
  st.info(
      "👈 사이드바에서 수주 및 출고 관리 데이터 파일(.xlsx 또는 .csv)을"
      " 업로드해 주세요."
  )
