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

# 다국어 텍스트 사전
LANG_DICT = {
    "한국어": {
        "title": "📦 본사 문직 제품 수주 및 출고 관리 시스템",
        "subtitle": "실시간 구글 스프레드시트 연동 대시보드 (보안 로그인 적용)",
        "sec_menu": "🔐 보안 및 로그인",
        "pw_label": "비밀번호 입력",
        "pw_placeholder": "비밀번호를 입력하세요",
        "admin_success": "🔓 최고 관리자 모드로 접속 중입니다.",
        "general_success": "🔓 일반 조회 모드로 접속 중입니다.",
        "pw_error": "❌ 비밀번호가 올바르지 않습니다.",
        "login_btn": "로그인",
        "logout_btn": "로그아웃",
        "refresh_btn": "🔄 데이터 새로고침",
        "menu_1": "📊 대시보드",
        "menu_2": "📅 출고 캘린더",
        "menu_3": "🏢 상세 이력",
        "menu_4": "📈 비교 분석",
        "menu_5": "📝 메모",
        "menu_6": "📈 방문자 통계 (관리자 전용)",
        "search_box": "검색",
    },
    "English": {
        "title": "📦 HQ Textile Order & Shipment Management System",
        "subtitle": "Real-time Google Sheets Dashboard (Secure Login)",
        "sec_menu": "🔐 Security & Login",
        "pw_label": "Enter Password",
        "pw_placeholder": "Enter password",
        "admin_success": "🔓 Admin mode active.",
        "general_success": "🔓 General view mode active.",
        "pw_error": "❌ Incorrect password.",
        "login_btn": "Login",
        "logout_btn": "Logout",
        "refresh_btn": "🔄 Refresh Data",
        "menu_1": "📊 Dashboard",
        "menu_2": "📅 Shipment Calendar",
        "menu_3": "🏢 History",
        "menu_4": "📈 Analysis",
        "menu_5": "📝 Memos",
        "menu_6": "📈 Visitor Stats (Admin Only)",
        "search_box": "Search",
    },
}

# 세션 상태 초기화
if "role" not in st.session_state:
  st.session_state.role = "logged_out"
if "visited_this_session" not in st.session_state:
  st.session_state.visited_this_session = False
if "daily_visitors" not in st.session_state:
  st.session_state.daily_visitors = {datetime.now().strftime("%Y-%m-%d"): 0}
if "access_logs" not in st.session_state:
  st.session_state.access_logs = []

# 사이드바 언어 선택
st.sidebar.markdown("---")
selected_lang = st.sidebar.selectbox("🌐 Language", ["한국어", "English"])
t = LANG_DICT[selected_lang]

GENERAL_PW = "songwol1234"
ADMIN_PW = "diaksp007099"

# 🔒 [로그아웃 상태인 경우]: 로그인 화면만 표시
if st.session_state.role == "logged_out":
  if logo_base64:
    st.markdown(
        f"""
        <div class="brand-logo-container">
            <img src="data:image/png;base64,{logo_base64}" class="brand-logo" alt="SONGWOL">
        </div>
        """,
        unsafe_allow_html=True,
    )
  st.markdown(
      f'<div class="main-header">{t["title"]}</div>', unsafe_allow_html=True
  )
  st.markdown(
      f'<div class="sub-header">안전한 로그인을 위해 비밀번호를 입력해 주세요.</div>',
      unsafe_allow_html=True,
  )

  st.markdown("---")

  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    st.subheader("🔐 시스템 접근 인증")
    input_pw = st.text_input(
        t["pw_label"], type="password", placeholder=t["pw_placeholder"]
    )
    if st.button(t["login_btn"], use_container_width=True):
      if input_pw == ADMIN_PW:
        st.session_state.role = "admin"
        if not st.session_state.visited_this_session:
          st.session_state.visited_this_session = True
          today_str = datetime.now().strftime("%Y-%m-%d")
          if today_str not in st.session_state.daily_visitors:
            st.session_state.daily_visitors[today_str] = 0
          st.session_state.daily_visitors[today_str] += 1
        st.session_state.access_logs.insert(
            0, {
                "시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "구분": "관리자 로그인",
            }
        )
        st.rerun()
      elif input_pw == GENERAL_PW:
        st.session_state.role = "user"
        if not st.session_state.visited_this_session:
          st.session_state.visited_this_session = True
          today_str = datetime.now().strftime("%Y-%m-%d")
          if today_str not in st.session_state.daily_visitors:
            st.session_state.daily_visitors[today_str] = 0
          st.session_state.daily_visitors[today_str] += 1
        st.session_state.access_logs.insert(
            0, {
                "시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "구분": "일반 사용자 로그인",
            }
        )
        st.rerun()
      else:
        st.error(t["pw_error"])
  st.stop()

# ==========================================
# 🔓 [로그인 성공 이후 대시보드 영역]
# ==========================================

if logo_base64:
  st.markdown(
      f"""
    <div class="brand-logo-container">
        <img src="data:image/png;base64,{logo_base64}" class="brand-logo" alt="SONGWOL">
    </div>
    """,
      unsafe_allow_html=True,
  )

st.markdown(f'<div class="main-header">{t["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">{t["subtitle"]}</div>', unsafe_allow_html=True)

url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg859XPxWPmD549O0AVE7VCCXbqpuccsZ3oj1D55-CQARnPa3eBNRlrNg_-BX-Zh_LlYTgf_llh7oS/pub?output=csv"


@st.cache_data(ttl=60)
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
  st.sidebar.header(t["sec_menu"])
  if st.sidebar.button(t["refresh_btn"]):
    st.cache_data.clear()
    st.success("캐시가 초기화되었습니다.")

  role_msg = (
      t["admin_success"]
      if st.session_state.role == "admin"
      else t["general_success"]
  )
  st.sidebar.success(role_msg)
  if st.sidebar.button(t["logout_btn"]):
    st.session_state.role = "logged_out"
    st.rerun()

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
  width_col = find_col(["cm", "폭", "규격", "사이즈"])

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

  # 날짜 파싱 안전하게 처리
  if date_col and date_col in df.columns:
    df["__PARSED_DATE"] = pd.to_datetime(df[date_col], errors="coerce")
  else:
    df["__PARSED_DATE"] = pd.NaT

  if order_date_col and order_date_col in df.columns:
    df["__ORDER_DATE"] = pd.to_datetime(df[order_date_col], errors="coerce")
    df["__ORDER_YEAR"] = df["__ORDER_DATE"].dt.year.fillna(0).astype(int)
    df["__ORDER_MONTH"] = df["__ORDER_DATE"].dt.to_period("M").astype(str)
  else:
    df["__ORDER_YEAR"] = 0
    df["__ORDER_MONTH"] = ""


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

  menu_list = [
      t["menu_1"],
      t["menu_2"],
      t["menu_3"],
      t["menu_4"],
      t["menu_5"],
  ]
  if st.session_state.role == "admin":
    menu_list.append(t["menu_6"])

  menu = st.sidebar.radio("Menu", menu_list)
  today = pd.to_datetime(datetime.today().date())

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
            search_query, na=False, case=False
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
    # 📅 업그레이드된 출고 캘린더 기능
    st.subheader("📅 Shipment Calendar (월별 출고 일정 캘린더)")
    st.markdown(
        "연도와 월을 선택하여 해당 기간 내에 출고되는 오더 일정을 날짜별로"
        " 확인하세요."
    )

    if date_col in df.columns:
      valid_cal_df = df.dropna(subset=["__PARSED_DATE"]).copy()
      if not valid_cal_df.empty:
        valid_cal_df["YearMonth"] = (
            valid_cal_df["__PARSED_DATE"].dt.to_period("M").astype(str)
        )
        ym_list = sorted(valid_cal_df["YearMonth"].unique(), reverse=True)

        selected_ym = st.selectbox(
            "📅 조회할 연도-월 선택 (Year-Month)", ym_list
        )
        month_df = valid_cal_df[
            valid_cal_df["YearMonth"] == selected_ym
        ].sort_values(by="__PARSED_DATE")

        # 요약 지표
        m_pcs = month_df["__PCS_NUM"].sum()
        m_kg = month_df["__KG_NUM"].sum()
        c1, c2, c3 = st.columns(3)
        with c1:
          st.metric("해당월 총 오더 건수", f"{len(month_df):,} 건")
        with c2:
          st.metric("해당월 총 수량", f"{m_pcs:,.0f} PCS")
        with c3:
          st.metric("해당월 총 중량", f"{m_kg:,.1f} Kg")

        st.markdown("---")

        # 날짜별 그룹 요약 및 상세 보기 탭
        tab_a, tab_b = st.tabs(
            ["📋 날짜별 출고 오더 상세 목록", "📊 일자별 물동량 요약"]
        )

        with tab_a:
          display_m_df = month_df.drop(
              columns=[
                  "__PARSED_DATE",
                  "__ORDER_DATE",
                  "__ORDER_YEAR",
                  "__ORDER_MONTH",
                  "__PCS_NUM",
                  "__KG_NUM",
                  "YearMonth",
              ],
              errors="ignore",
          )
          st.dataframe(format_df_dates(display_m_df), use_container_width=True)

        with tab_b:
          daily_summary = (
              month_df.groupby(month_df["__PARSED_DATE"].dt.strftime("%Y-%m-%d"))
              .agg(
                  Orders=("__PCS_NUM", "count"),
                  Total_Pcs=("__PCS_NUM", "sum"),
                  Total_Kg=("__KG_NUM", "sum"),
              )
              .reset_index()
              .rename(columns={"__PARSED_DATE": "출고일자"})
          )
          st.dataframe(daily_summary, use_container_width=True)
          st.bar_chart(daily_summary.set_index("출고일자")["Total_Pcs"])

      else:
        st.warning("캘린더에 표시할 유효한 날짜 데이터가 없습니다.")
    else:
      st.warning(
          "스프레드시트에서 날짜(납기일) 관련 컬럼을 찾을 수 없습니다."
      )

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
    st.subheader("📈 종합 멀티 조건 복합 필터 분석 시스템 (발주일 기준)")
    st.markdown(
        "원하시는 조건들을 **동시에 여러 개 선택(Multi-select)**하여 복합"
        " 검색하세요."
    )

    f_col1, f_col2, f_col3 = st.columns(3)

    with f_col1:
      available_years = (
          sorted([y for y in df["__ORDER_YEAR"].unique() if y > 0])
          if "__ORDER_YEAR" in df.columns
          else []
      )
      sel_years = st.multiselect(
          "📅 연도별 (Year)", available_years, placeholder="전체 연도"
      )

      available_months = (
          sorted(df[df["__ORDER_MONTH"] != ""]["__ORDER_MONTH"].unique().tolist())
          if "__ORDER_MONTH" in df.columns
          else []
      )
      sel_months = st.multiselect(
          "🗓️ 월별 (Month)", available_months, placeholder="전체 월"
      )

      available_agencies = (
          sorted(df[agency_col].dropna().unique().tolist())
          if agency_col and agency_col in df.columns
          else []
      )
      sel_agencies = st.multiselect(
          "🏢 대리점별 (Agency)", available_agencies, placeholder="전체 대리점"
      )

    with f_col2:
      available_ships = (
          sorted(df[ship_col].dropna().unique().tolist())
          if ship_col and ship_col in df.columns
          else []
      )
      sel_ships = st.multiselect(
          "🚢 출하처별 (Shipment)", available_ships, placeholder="전체 출하처"
      )

      available_yarns = (
          sorted(df[yarn_col].dropna().unique().tolist())
          if yarn_col and yarn_col in df.columns
          else []
      )
      sel_yarns = st.multiselect(
          "🧵 YARN(사종)별", available_yarns, placeholder="전체 사종"
      )

      available_products = (
          sorted(df[product_col].dropna().unique().tolist())
          if product_col and product_col in df.columns
          else []
      )
      sel_products = st.multiselect(
          "🏷️ 아이템별 (Product)", available_products, placeholder="전체 아이템"
      )

    with f_col3:
      available_widths = (
          sorted(df[width_col].dropna().unique().tolist())
          if width_col and width_col in df.columns
          else []
      )
      sel_widths = st.multiselect(
          "📏 규격/폭별 (Width)", available_widths, placeholder="전체 규격"
      )

      available_status = (
          sorted(df[completed_col].dropna().unique().tolist())
          if completed_col and completed_col in df.columns
          else []
      )
      sel_status = st.multiselect(
          "✅ 출고 완료 여부 (O/기타)",
          available_status,
          placeholder="전체 상태",
      )

      st.markdown("⚖️ **수량 및 중량 상세 범위**")
      min_pcs, max_pcs = (
          int(df["__PCS_NUM"].min()),
          int(df["__PCS_NUM"].max()),
      )
      pcs_range = st.slider(
          "장수 (PCS) 범위", min_value=min_pcs, max_value=max_pcs, value=(min_pcs, max_pcs)
      )

      min_kg, max_kg = float(df["__KG_NUM"].min()), float(df["__KG_NUM"].max())
      if min_kg == max_kg:
        max_kg = min_kg + 1.0
      kg_range = st.slider(
          "중량 (Kg) 범위",
          min_value=min_kg,
          max_value=max_kg,
          value=(min_kg, max_kg),
      )

    filtered_analysis_df = df.copy()

    if sel_years:
      filtered_analysis_df = filtered_analysis_df[
          filtered_analysis_df["__ORDER_YEAR"].isin(sel_years)
      ]
    if sel_months:
      filtered_analysis_df = filtered_analysis_df[
          filtered_analysis_df["__ORDER_MONTH"].isin(sel_months)
      ]
    if sel_agencies and agency_col:
      filtered_analysis_df = filtered_analysis_df[
          filtered_analysis_df[agency_col].isin(sel_agencies)
      ]
    if sel_ships and ship_col:
      filtered_analysis_df = filtered_analysis_df[
          filtered_analysis_df[ship_col].isin(sel_ships)
      ]
    if sel_yarns and yarn_col:
      filtered_analysis_df = filtered_analysis_df[
          filtered_analysis_df[yarn_col].isin(sel_yarns)
      ]
    if sel_products and product_col:
      filtered_analysis_df = filtered_analysis_df[
          filtered_analysis_df[product_col].isin(sel_products)
      ]
    if sel_widths and width_col:
      filtered_analysis_df = filtered_analysis_df[
          filtered_analysis_df[width_col].isin(sel_widths)
      ]
    if sel_status and completed_col:
      filtered_analysis_df = filtered_analysis_df[
          filtered_analysis_df[completed_col].isin(sel_status)
      ]

    filtered_analysis_df = filtered_analysis_df[
        (filtered_analysis_df["__PCS_NUM"] >= pcs_range[0])
        & (filtered_analysis_df["__PCS_NUM"] <= pcs_range[1])
        & (filtered_analysis_df["__KG_NUM"] >= kg_range[0])
        & (filtered_analysis_df["__KG_NUM"] <= kg_range[1])
    ]

    st.markdown("---")
    st.subheader(
        f"📊 멀티 복합 필터 검색 결과 (총 {len(filtered_analysis_df):,}건)"
    )

    if not filtered_analysis_df.empty:
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

      st.markdown("### 💡 AI 멀티 복합 조건 분석 요약 코멘트")
      active_conditions = []
      if sel_years:
        active_conditions.append(f"연도: {list(sel_years)}")
      if sel_months:
        active_conditions.append(f"월: {list(sel_months)}")
      if sel_agencies:
        active_conditions.append(f"대리점: {list(sel_agencies)}")
      if sel_ships:
        active_conditions.append(f"출하처: {list(sel_ships)}")
      if sel_yarns:
        active_conditions.append(f"사종: {list(sel_yarns)}")
      if sel_products:
        active_conditions.append(f"아이템: {list(sel_products)}")
      if sel_widths:
        active_conditions.append(f"규격: {list(sel_widths)}")
      if sel_status:
        active_conditions.append(f"출고상태: {list(sel_status)}")

      cond_str = (
          ", ".join(active_conditions)
          if active_conditions
          else "전체 조건 (기본 범위)"
      )

      comment = f"""
            > **[종합 복합 조건 분석 리포트]**
            > - **적용된 다중 조건**: {cond_str}
            > - **수량 및 중량 범위**: PCS({pcs_range[0]} ~ {pcs_range[1]}), Kg({kg_range[0]:,.1f} ~ {kg_range[1]:,.1f})
            > - **조회된 총 오더 건수**: {len(filtered_analysis_df):,}건
            > - **누적 집계**: 총 수량 **{tot_pcs:,.0f} PCS**, 총 중량 **{tot_kg:,.1f} Kg**이 집계되었습니다.
            > - 캘린더 기능과 보안 로그인, 캐싱이 완벽하게 연동되어 있습니다.
            """
      st.markdown(comment)

    else:
      st.warning("선택하신 다중 복합 조건에 일치하는 오더 데이터가 없습니다.")

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

  # 📈 방문자 통계 메뉴 (최고 관리자 전용)
  elif menu == t["menu_6"] and st.session_state.role == "admin":
    st.subheader("📈 관리자 전용 날짜별 방문자 통계 및 접속 로그")
    st.markdown(
        "최고 관리자(`diaksp007099`) 권한으로 접속하여 세션 기반 일자별 방문"
        " 현황을 모니터링합니다."
    )

    total_visitors = sum(st.session_state.daily_visitors.values())

    v_col1, v_col2 = st.columns(2)
    with v_col1:
      st.metric(label="총 누적 방문자수 (세션 기준)", value=f"{total_visitors:,} 명")
    with v_col2:
      st.metric(label="현재 접속 권한", value="최고 관리자 (Admin)")

    st.markdown("---")
    st.subheader("📅 날짜별 방문자 통계 분석")
    daily_df = pd.DataFrame(
        list(st.session_state.daily_visitors.items()),
        columns=["방문 일자", "방문자 수"],
    ).sort_values(by="방문 일자", ascending=False)
    st.dataframe(daily_df, use_container_width=True)
    st.bar_chart(daily_df.set_index("방문 일자")["방문자 수"])

    st.markdown("---")
    st.subheader("📋 최근 시스템 접속 및 인증 로그")
    log_df = pd.DataFrame(st.session_state.access_logs)
    st.dataframe(log_df, use_container_width=True)

except Exception as e:
  st.error(f"Error: {e}")
