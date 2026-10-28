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
st.markdown('<div class="sub-header">실시간 SCM 대시보드 (파일 업로드 공유 버전)</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.subheader("📁 데이터 파일 업로드")
uploaded_file = st.sidebar.file_uploader("엑셀(.xlsx) 또는 CSV 파일 선택", type=["csv", "xlsx"])

if uploaded_file is None:
    st.info("👋 **[안내]** 대시보드를 시작하려면 왼쪽 사이드바의 **[파일 업로드]** 버튼을 눌러 엑셀 파일을 업로드해 주세요!")
    st.stop()

# 엑셀 파일 그대로 원본 읽기 (가공 및 변형 없음)
try:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # 컬럼 공백만 살짝 다듬기
    df.columns = df.columns.astype(str).str.strip()

    st.sidebar.markdown("---")
    st.sidebar.success("✅ 파일이 성공적으로 업로드되었습니다!")

    # 검색 기능
    search_query = st.text_input("🔍 검색 (내용 입력)", "")
    filtered_df = df.copy()
    if search_query:
        cond = pd.Series(False, index=filtered_df.index)
        for col in filtered_df.columns:
            cond = cond | filtered_df[col].astype(str).str.contains(search_query, na=False, case=False)
        filtered_df = filtered_df[cond]

    # 업로드한 엑셀 모양 그대로 화면에 출력
    st.dataframe(filtered_df, width='stretch', height=600)

except Exception as e:
    st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
