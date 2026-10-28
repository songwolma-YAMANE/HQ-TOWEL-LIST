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

# 엑셀 파일 원본 그대로 정확하게 읽기 (Header를 첫 번째 행으로 지정)
try:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, header=0)
    else:
        df = pd.read_excel(uploaded_file, header=0)
    
    # 불필요한 빈 컬럼(Unnamed) 정리 및 컬럼명 공백 다듬기
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.columns = df.columns.astype(str).str.strip()

    # 날짜 컬럼들에 불필요한 '00:00:00' 문자열이 붙는 경우 깔끔하게 날짜만 표시되도록 변환
    for col in df.columns:
        if any(k in col for k in ['납기', '일자', '날짜', '수령']):
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d').fillna(df[col].astype(str))
            df[col] = df[col].replace(['NaT', 'nan', 'NaT 00:00:00'], '')

    st.sidebar.markdown("---")
    st.sidebar.success("✅ 파일이 성공적으로 업로드되었습니다!")

    # 검색 기능 (출하처, 제품명 등 원하는 키워드로 검색 가능)
    search_query = st.text_input("🔍 검색 (출하처, 제품명, 대리점 등 입력)", "")
    filtered_df = df.copy()
    if search_query:
        cond = pd.Series(False, index=filtered_df.index)
        for col in filtered_df.columns:
            cond = cond | filtered_df[col].astype(str).str.contains(search_query, na=False, case=False)
        filtered_df = filtered_df[cond]

    # 업로드한 엑셀 파일 원본 그대로 화면에 출력 (폭, 중량, 단가 등 모든 항목 완벽 표시)
    st.dataframe(filtered_df, width='stretch', height=650)

except Exception as e:
    st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
