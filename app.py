import pandas as pd
import streamlit as st

st.sidebar.title("데이터 소스 설정")
uploaded_file = st.sidebar.file_uploader(
    "수주/출고 데이터 파일 업로드 (Excel / CSV)", type=["xlsx", "csv"]
)

if uploaded_file is not None:
  if uploaded_file.name.endswith(".csv"):
    # CSV의 경우, 제목이 2번째 줄에 있다면 header=1 지정
    df = pd.read_csv(uploaded_file, header=1)
  else:
    # 엑셀 파일의 경우, 제목이 있는 행 번호 지정 (예: 2번째 줄이면 header=1, 3번째 줄이면 header=2)
    df = pd.read_excel(uploaded_file, header=1)

  st.success("데이터를 성공적으로 불러왔습니다!")

  # 데이터 확인용 (필요시 'Unnamed' 컬럼 제거 등 추가 가공 가능)
  st.dataframe(df)
else:
  st.info(
      "👈 사이드바에서 수주 및 출고 관리 데이터 파일(.xlsx 또는 .csv)을"
      " 업로드해 주세요."
  )
