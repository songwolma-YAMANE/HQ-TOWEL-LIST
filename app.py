from datetime import datetime, timedelta
import io
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
    st.info("👋 **[안내]** 대시보드를 시작하려면 왼쪽 사이드바의 **[파일 업로드]** 버튼을 눌러 수주/출고 관리 엑셀(.xlsx) 파일을 업로드해 주세요!")
    st.stop()

# 파일 읽기 및 진짜 제목 행(Header) 자동 탐색
try:
    if uploaded_file.name.endswith('.csv'):
        df_temp = pd.read_csv(uploaded_file, header=None)
    else:
        df_temp = pd.read_excel(uploaded_file, header=None)

    # '확정납기'나 '대리점', '출하처' 등의 핵심 단어가 포함된 행을 진짜 헤더로 지정
    header_row = 0
    for i in range(min(15, len(df_temp))):
        row_str = str(df_temp.iloc[i].values)
        if any(keyword in row_str for keyword in ['납기', '대리점', '출하처', '발주서', 'DELIVERY', 'AGENCY']):
            header_row = i
            break

    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, header=header_row)
    else:
        df = pd.read_excel(uploaded_file, header=header_row)
        
    df.columns = df.columns.astype(str).str.strip()
except Exception as e:
    st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
    st.stop()

try:
    def find_col(keywords):
        for col in df.columns:
            for kw in keywords:
                if kw.lower() in col.lower():
                    return col
        return None

    date_col = find_col(['확정납기 1차', 'DELIVERY 1', '납기'])
    agency_col = find_col(['대리점', 'AGENCY'])
    ship_col = find_col(['출하처', 'SHIPMENT'])
    product_col = find_col(['제품명', 'KOREAN NAME'])
    completed_col = find_col(['출고 완료', '출고완료'])
    
    kg_col = find_col(['order kg', 'kg', '중량'])
    df['__KG_NUM'] = pd.to_numeric(df[kg_col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0) if (kg_col and kg_col in df.columns) else 0

    # 날짜 데이터 뒤의 00:00:00 깔끔하게 제거하는 함수
    def format_df_dates(input_df):
        d_df = input_df.copy()
        for col in d_df.columns:
            # 컬럼 이름에 '날기', '납기', '일자', 'Date', 'Delivery' 등이 들어가거나 데이터 타입이 날짜인 경우
            if any(k in col for k in ['납기', '일자', '날짜', 'Date', 'DELIVERY', '수령']):
                d_df[col] = pd.to_datetime(d_df[col], errors='coerce').dt.strftime('%Y-%m-%d').fillna(d_df[col].astype(str))
                d_df[col] = d_df[col].replace(['NaT', 'nan', 'NaT 00:00:00'], '')
        return d_df

    st.sidebar.markdown("---")
    menu = st.sidebar.selectbox("Menu", ["📊 대시보드", "📅 캘린더", "🏢 상세 이력", "📈 비교 분석"])

    if menu == "📊 대시보드":
        total_len = len(df)
        completed_count = len(df[df[completed_col].astype(str).str.upper() == 'O']) if (completed_col and completed_col in df.columns) else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Orders", f"{total_len:,}")
        with col2:
            st.metric("Completed", f"{completed_count:,}")
        with col3:
            rate = int((completed_count / total_len * 100) if total_len > 0 else 0)
            st.metric("Completion Rate", f"{rate}%")

        st.markdown("---")
        st.subheader("Order List")
        search_query = st.text_input("Search Shipment or Product", "")
        filtered_df = df.copy()
        if search_query:
            cond = pd.Series(False, index=filtered_df.index)
            if ship_col in filtered_df.columns:
                cond = cond | filtered_df[ship_col].astype(str).str.contains(search_query, na=False, case=False)
            if product_col in filtered_df.columns:
                cond = cond | filtered_df[product_col].astype(str).str.contains(search_query, na=False, case=False)
            filtered_df = filtered_df[cond]

        # 폭, 중량, 단가 등 모든 컬럼이 포함된 전체 데이터프레임을 날짜 포맷만 깔끔하게 다듬어서 출력
        st.data_editor(format_df_dates(filtered_df), width='stretch')

    elif menu == "📅 캘린더":
        st.subheader("Shipment Calendar")
        if date_col in df.columns:
            valid_df = df.dropna(subset=[date_col]).copy()
            valid_df['YearMonth'] = pd.to_datetime(valid_df[date_col], errors='coerce').dt.to_period('M').astype(str)
            ym_list = sorted([ym for ym in valid_df['YearMonth'].unique() if ym != 'NaT'], reverse=True)
            if ym_list:
                selected_ym = st.selectbox("Select Year-Month", ym_list)
                st.dataframe(format_df_dates(valid_df[valid_df['YearMonth'] == selected_ym]), width='stretch')
            else:
                st.warning("No date data.")
        else:
            st.warning("Date column not found.")

    elif menu == "🏢 상세 이력":
        st.subheader("Agency History")
        if agency_col in df.columns:
            selected_target = st.selectbox("Select Agency", df[agency_col].dropna().unique())
            st.dataframe(format_df_dates(df[df[agency_col] == selected_target]), width='stretch')
        else:
            st.warning("Agency column not found.")

    elif menu == "📈 비교 분석":
        st.subheader("Comparative Analysis")
        if date_col in df.columns:
            df['__YEAR'] = pd.to_datetime(df[date_col], errors='coerce').dt.year.fillna(0).astype(int)
            yearly_summary = df[df['__YEAR'] > 0].groupby('__YEAR').agg({'__YEAR': 'count', '__KG_NUM': 'sum'}).rename(columns={'__YEAR': 'Orders', '__KG_NUM': 'Total_Kg'}).reset_index()
            st.dataframe(yearly_summary, width='stretch')
            if not yearly_summary.empty:
                st.bar_chart(yearly_summary.set_index('__YEAR')['Orders'])
        else:
            st.warning("Year data not available.")

except Exception as e:
    st.error(f"대시보드 실행 중 오류 발생: {e}")
