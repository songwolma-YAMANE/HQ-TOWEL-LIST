from datetime import datetime, timedelta
import io
import base64
from PIL import Image
import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (와이드 레이아웃)
st.set_page_config(
    page_title="HQ Textile Order & Shipment Management", layout="wide"
)

# HTML/CSS 커스텀 디자인 적용
st.markdown(
    """
<style>
.main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem; }
.sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
.stAlert { border-radius: 0.5rem; }

.brand-logo-container {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
}
.brand-logo {
    height: 40px;
    width: auto;
    object-fit: contain;
}
</style>
""",
    unsafe_allow_html=True,
)


# 로고 이미지를 읽어와서 Base64로 변환하는 함수
def get_resized_image_base64(image_path, target_height=40):
  try:
    img = Image.open(image_path)
    original_width, original_height = img.size
    aspect_ratio = original_width / original_height
    target_width = int(target_height * aspect_ratio)

    img_resized = img.resize(
        (target_width, target_height), Image.Resampling.LANCZOS
    )
    buffered = io.BytesIO()
    img_resized.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()
  except Exception:
    return ""


# 하나의 로고만 깔끔하게 출력
logo_base64 = get_resized_image_base64("logo_korea.png", target_height=40)

if logo_base64:
  st.markdown(
      f"""
    <div class="brand-logo-container">
        <img src="data:image/png;base64,{logo_base64}" class="brand-logo" alt="SONGWOL">
    </div>
    """,
      unsafe_allow_html=True,
  )

# 다국어 텍스트 사전
LANG_DICT = {
    "한국어": {
        "title": "📦 본사 문직 제품 수주 및 출고 관리 시스템",
        "subtitle": "실시간 구글 스프레드시트 연동 대시보드",
        "sec_menu": "🔐 보안 및 시스템 메뉴",
        "pw_label": "관리자 비밀번호 입력",
        "pw_placeholder": "비밀번호",
        "admin_success": "🔓 관리자 모드 활성화",
        "pw_error": "❌ 비밀번호 오류",
        "general_info": "💡 일반 조회 모드",
        "menu_1": "📊 대시보드",
        "menu_2": "📅 캘린더",
        "menu_3": "🏢 상세 이력",
        "menu_4": "📈 비교 분석",
        "menu_5": "📝 메모",
        "search_box": "검색",
        "excel_btn": "엑셀 다운로드",
    },
    "English": {
        "title": "📦 HQ Textile Order & Shipment Management System",
        "subtitle": "Real-time Google Sheets Dashboard",
        "sec_menu": "🔐 Security & System Menu",
        "pw_label": "Enter Admin Password",
        "pw_placeholder": "Password",
        "admin_success": "🔓 Admin mode activated",
        "pw_error": "❌ Incorrect password",
        "general_info": "💡 General view mode",
        "menu_1": "📊 Dashboard",
        "menu_2": "📅 Calendar",
        "menu_3": "🏢 History",
        "menu_4": "📈 Analysis",
        "menu_5": "📝 Memos",
        "search_box": "Search",
        "excel_btn": "Download Excel",
    },
}

# 사이드바 언어 선택
st.sidebar.markdown("---")
selected_lang = st.sidebar.selectbox("🌐 Language", ["한국어", "English"])
t = LANG_DICT[selected_lang]

# 타이틀 적용
st.markdown(f'<div class="main-header">{t["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">{t["subtitle"]}</div>', unsafe_allow_html=True)

# 구글 스프레드시트 CSV 링크
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg859XPxWPmD549O0AVE7VCCXbqpuccsZ3oj1D55-CQARnPa3eBNRlrNg_-BX-Zh_LlYTgf_llh7oS/pub?output=csv"


@st.cache_data(ttl=30)
def load_data():
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      )
  }
  res = requests.get(url, headers=headers)
  res.raise_for_status()
  df_temp = pd.read_csv(io.BytesIO(res.content), header=None)
  header_row = 0
  for i in range(len(df_temp)):
    row_str = str(df_temp.iloc[i].values)
    if "출하처" in row_str or "SHIPMENT" in row_str or "제품명" in row_str:
      header_row = i
      break
  data_df = pd.read_csv(io.BytesIO(res.content), header=header_row)
  data_df.columns = data_df.columns.astype(str).str.strip()
  return data_df


try:
  df = load_data()


  def find_col(keywords):
    for col in df.columns:
      for kw in keywords:
        if kw.lower() in col.lower():
          return col
    return None


  date_col = find_col(["확정납기 1차", "DELIVERY 1", "납기"])
  agency_col = find_col(["대리점", "AGENCY"])
  ship_col = find_col(["출하처", "SHIPMENT"])
  product_col = find_col(["제품명", "KOREAN NAME", "품명"])
  completed_col = find_col(["출고 완료", "출고완료"])
  order_date_col = find_col(["발주서 수령", "발주서", "수령일"])
  yarn_col = find_col(["yarn", "사종", "번수", "pile", "실"])

  pcs_col = find_col(["order pcs", "pcs", "수량", "장수"])
  kg_col = find_col(["order kg", "kg", "중량"])

  df["__PCS_NUM"] = (
      pd.to_numeric(
          df[pcs_col].astype(str).str.replace(r"[^0-9.]", "", regex=True),
          errors="coerce",
      ).fillna(0)
      if pcs_col and pcs_col in df.columns
      else 1
  )
  df["__KG_NUM"] = (
      pd.to_numeric(
          df[kg_col].astype(str).str.replace(r"[^0-9.]", "", regex=True),
          errors="coerce",
      ).fillna(0)
      if kg_col and kg_col in df.columns
      else 0
  )


  def format_df_dates(input_df):
    d_df = input_df.copy()
    if date_col and date_col in d_df.columns:
      d_df[date_col] = (
          pd.to_datetime(d_df[date_col], errors="coerce")
          .dt.strftime("%Y-%m-%d")
          .fillna("")
      )
      d_df[date_col] = d_df[date_col].replace("NaT", "")
    if order_date_col and order_date_col in d_df.columns:
      d_df[order_date_col] = (
          pd.to_datetime(d_df[order_date_col], errors="coerce")
          .dt.strftime("%Y-%m-%d")
          .fillna("")
      )
      d_df[order_date_col] = d_df[order_date_col].replace("NaT", "")
    return d_df


  if "order_memos" not in st.session_state:
    st.session_state.order_memos = {}

  st.sidebar.header(t["sec_menu"])
  ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "songwol1234")
  input_pw = st.sidebar.text_input(
      t["pw_label"], type="password", placeholder=t["pw_placeholder"]
  )
  is_admin = input_pw == ADMIN_PASSWORD

  if is_admin:
    st.sidebar.success(t["admin_success"])
  else:
    if input_pw:
      st.sidebar.error(t["pw_error"])
    else:
      st.sidebar.info(t["general_info"])

  menu = st.sidebar.radio(
      "Menu",
      [t["menu_1"], t["menu_2"], t["menu_3"], t["menu_4"], t["menu_5"]],
  )
  today = pd.to_datetime(datetime.today().date())

  if date_col and date_col in df.columns:
    df["__PARSED_DATE"] = pd.to_datetime(df[date_col], errors="coerce")

  if order_date_col and order_date_col in df.columns:
    df["__ORDER_DATE"] = pd.to_datetime(df[order_date_col], errors="coerce")
    df["__ORDER_YEAR"] = df["__ORDER_DATE"].dt.year.fillna(0).astype(int)
    df["__ORDER_MONTH"] = df["__ORDER_DATE"].dt.to_period("M").astype(str)
  else:
    df["__ORDER_YEAR"] = 0
    df["__ORDER_MONTH"] = ""

  if menu == t["menu_1"]:
    total_len = len(df)
    completed_count = (
        len(df[df[completed_col].astype(str).str.upper() == "O"])
        if (completed_col and completed_col in df.columns)
        else 0
    )

    col1, col2, col3 = st.columns(3)
    with col1:
      st.metric("Total Orders", f"{total_len:,}")
    with col2:
      st.metric("Completed", f"{completed_count:,}")
    with col3:
      rate = int((completed_count / total_len * 100) if total_len > 0 else 0)
      st.metric("Completion Rate", f"{rate}%")

    st.markdown("---")

    # 1. 7일 이내 출고 임박 리스트
    st.subheader("🚨 [긴급] 7일 이내 출고 임박 리스트")
    if date_col and date_col in df.columns:
      not_completed = (
          df[completed_col].astype(str).str.upper() != "O"
          if (completed_col and completed_col in df.columns)
          else pd.Series(True, index=df.index)
      )
      d7_df = df[
          not_completed
          & (df["__PARSED_DATE"] >= today)
          & (df["__PARSED_DATE"] <= today + timedelta(days=7))
      ].copy()

      if not d7_df.empty:
        st.warning(
            f"총 {len(d7_df)}건의 출고 임박 항목이 있습니다 (7일 이내 납기 도래)"
        )
        editor_d7 = d7_df.drop(
            columns=[
                "__PARSED_DATE",
                "__ORDER_DATE",
                "__ORDER_YEAR",
                "__ORDER_MONTH",
                "__PCS_NUM",
                "__KG_NUM",
            ],
            errors="ignore",
        )
        st.dataframe(format_df_dates(editor_d7), use_container_width=True)
      else:
        st.info("향후 7일 이내 출고 임박한 미완료 오더가 없습니다.")
    else:
      st.info("납기일(날짜) 컬럼을 찾을 수 없습니다.")

    st.markdown("---")

    # 2. 최근 7일 이내 신규 발주서 수령 아이템 리스트
    st.subheader("📥 [신규] 최근 7일 이내 발주서 수령 아이템")
    if order_date_col and order_date_col in df.columns:
      recent_orders = df[
          (df["__ORDER_DATE"] >= today - timedelta(days=7))
          & (df["__ORDER_DATE"] <= today)
      ].copy()

      if not recent_orders.empty:
        st.success(
            f"최근 7일 내 신규 접수된 발주서가 총 {len(recent_orders)}건 있습니다."
        )
        editor_recent = recent_orders.drop(
            columns=[
                "__PARSED_DATE",
                "__ORDER_DATE",
                "__ORDER_YEAR",
                "__ORDER_MONTH",
                "__PCS_NUM",
                "__KG_NUM",
            ],
            errors="ignore",
        )
        st.dataframe(format_df_dates(editor_recent), use_container_width=True)
      else:
        st.info("최근 7일 이내에 수령된 신규 발주서 항목이 없습니다.")
    else:
      st.info("발주서 수령일 컬럼을 찾을 수 없습니다.")

    st.markdown("---")
    st.subheader("Order List (전체 오더 목록)")
    search_query = st.text_input(t["search_box"], "")
    filtered_df = df.copy()
    if search_query:
      cond = pd.Series(False, index=filtered_df.index)
      if ship_col in filtered_df.columns:
        cond = cond | filtered_df[ship_col].astype(str).str.contains(
            search_query, na=False, case=False
        )
      if product_col in filtered_df.columns:
        cond = cond | filtered_df[product_col].astype(str).str.contains(
            search_query, nc=False, case=False
        )
      filtered_df = filtered_df[cond]

    editor_df = filtered_df.drop(
        columns=[
            "__PARSED_DATE",
            "__ORDER_DATE",
            "__ORDER_YEAR",
            "__ORDER_MONTH",
            "__PCS_NUM",
            "__KG_NUM",
        ],
        errors="ignore",
    )
    st.data_editor(format_df_dates(editor_df), use_container_width=True)

  elif menu == t["menu_2"]:
    st.subheader("Shipment Calendar")
    if date_col in df.columns:
      valid_df = df.dropna(subset=[date_col]).copy()
      valid_df["YearMonth"] = valid_df[date_col].dt.to_period("M").astype(str)
      ym_list = sorted(valid_df["YearMonth"].unique(), reverse=True)
      if ym_list:
        selected_ym = st.selectbox("Select Year-Month", ym_list)
        month_df = valid_df[valid_df["YearMonth"] == selected_ym]
        st.dataframe(format_df_dates(month_df), use_container_width=True)
      else:
        st.warning("No date data.")
    else:
      st.warning("Date column not found.")

  elif menu == t["menu_3"]:
    st.subheader("Agency History")
    if agency_col in df.columns:
      selected_target = st.selectbox(
          "Select Agency", df[agency_col].dropna().unique()
      )
      target_df = df[df[agency_col] == selected_target]
      st.dataframe(format_df_dates(target_df), use_container_width=True)
    else:
      st.warning("Agency column not found.")

  elif menu == t["menu_4"]:
    st.subheader("📈 멀티 조건 복합 필터 비교 분석 시스템 (발주일 기준)")

    st.markdown(
        "원하시는 조건들을 **동시에 여러 개 선택**하여 조합해 보세요. 선택한"
        " 조건에 맞는 상세 오더 내역과 요약 통계를 바로 확인하실 수 있습니다."
    )

    # 멀티 필터 입력 UI (2개 컬럼으로 배치하여 깔끔하게 구성)
    f_col1, f_col2 = st.columns(2)

    with f_col1:
      # 1. 연도 멀티 선택
      available_years = (
          sorted([y for y in df["__ORDER_YEAR"].unique() if y > 0])
          if "__ORDER_YEAR" in df.columns
          else []
      )
      sel_years = st.multiselect(
          "📅 연도 선택 (복수 선택 가능)", available_years
      )

      # 2. 대리점 멀티 선택
      available_agencies = (
          sorted(df[agency_col].dropna().unique().tolist())
          if agency_col and agency_col in df.columns
          else []
      )
      sel_agencies = st.multiselect(
          "🏢 대리점 선택 (복수 선택 가능)", available_agencies
      )

    with f_col2:
      # 3. YARN(사종) 멀티 선택
      available_yarns = (
          sorted(df[yarn_col].dropna().unique().tolist())
          if yarn_col and yarn_col in df.columns
          else []
      )
      sel_yarns = st.multiselect(
          "🧵 YARN(사종) 선택 (복수 선택 가능)", available_yarns
      )

      # 4. 아이템 이름 멀티 선택
      available_products = (
          sorted(df[product_col].dropna().unique().tolist())
          if product_col and product_col in df.columns
          else []
      )
      sel_products = st.multiselect(
          "🏷️ 아이템 이름 선택 (복수 선택 가능)", available_products
      )

    # 필터링 로직 적용
    filtered_analysis_df = df.copy()

    if sel_years:
      filtered_analysis_df = filtered_analysis_df[
          filtered_analysis_df["__ORDER_YEAR"].isin(sel_years)
      ]
    if sel_agencies and agency_col:
      filtered_analysis_df = filtered_analysis_df[
          filtered_analysis_df[agency_col].isin(sel_agencies)
      ]
    if sel_yarns and yarn_col:
      filtered_analysis_df = filtered_analysis_df[
          filtered_analysis_df[yarn_col].isin(sel_yarns)
      ]
    if sel_products and product_col:
      filtered_analysis_df = filtered_analysis_df[
          filtered_analysis_df[product_col].isin(sel_products)
      ]

    st.markdown("---")
    st.subheader(
        f"📊 복합 필터 검색 결과 (총 {len(filtered_analysis_df):,}건)"
    )

    if not filtered_analysis_df.empty:
      # 합계 지표 표시
      tot_pcs = filtered_analysis_df["__PCS_NUM"].sum()
      tot_kg = filtered_analysis_df["__KG_NUM"].sum()

      m_col1, m_col2, m_col3 = st.columns(3)
      with m_col1:
        st.metric("Matching Orders", f"{len(filtered_analysis_df):,} 건")
      with m_col2:
        st.metric("Total PCS", f"{tot_pcs:,.0f} PCS")
      with m_col3:
        st.metric("Total Weight", f"{tot_kg:,.1f} Kg")

      st.markdown("")

      # 결과 데이터프레임 표시 (내부 시스템 컬럼 제외)
      display_analysis_df = filtered_analysis_df.drop(
          columns=[
              "__PARSED_DATE",
              "__ORDER_DATE",
              "__ORDER_YEAR",
              "__ORDER_MONTH",
              "__PCS_NUM",
              "__KG_NUM",
          ],
          errors="ignore",
      )
      st.dataframe(
          format_df_dates(display_analysis_df), use_container_width=True
      )

      # AI 자동 분석 리포트 코멘트
      st.markdown("### 💡 AI 멀티 조건 분석 요약 코멘트")
      active_conditions = []
      if sel_years:
        active_conditions.append(f"연도: {list(sel_years)}")
      if sel_agencies:
        active_conditions.append(f"대리점: {list(sel_agencies)}")
      if sel_yarns:
        active_conditions.append(f"사종: {list(sel_yarns)}")
      if sel_products:
        active_conditions.append(f"아이템: {list(sel_products)}")

      cond_str = (
          ", ".join(active_conditions)
          if active_conditions
          else "전체 조건 (필터 없음)"
      )

      comment = f"""
            > **[복합 조건 분석 리포트]**
            > - **적용된 검색 조건**: {cond_str}
            > - **조회된 총 오더 건수**: {len(filtered_analysis_df):,}건
            > - **누적 수량 및 중량**: 총 수량 **{tot_pcs:,.0f} PCS**, 총 중량 **{tot_kg:,.1f} Kg**이 집계되었습니다.
            > - 다중 필터를 통해 원하시는 특정 년도, 대리점, 사종별 데이터를 정확하게 추출하여 비교 검토하실 수 있습니다.
            """
      st.markdown(comment)

    else:
      st.warning(
          "선택하신 복합 조건에 일치하는 오더 데이터가 없습니다. 필터를"
          " 조절해 주세요."
      )

  elif menu == t["menu_5"]:
    st.subheader("Staff Memos")
    if ship_col and product_col in df.columns:
      df["오더표시"] = (
          df.index.astype(str)
          + " | "
          + df[ship_col].astype(str)
          + " | "
          + df[product_col].astype(str)
      )
      selected_label = st.selectbox("Select Order", df["오더표시"].tolist())
      idx = int(selected_label.split(" | ")[0])
      memo = st.text_area(
          "Enter Memo", value=st.session_state.order_memos.get(idx, "")
      )
      if st.button("Save Memo"):
        st.session_state.order_memos[idx] = memo
        st.success("Saved!")
    else:
      st.warning("Required columns not found.")
except Exception as e:
  st.error(f"Error: {e}")
