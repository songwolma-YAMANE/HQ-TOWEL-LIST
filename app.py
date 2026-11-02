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
        "agency_filter": "대리점 선택",
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
        "agency_filter": "Agency Filter",
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

# 새로운 웹에 게시된 구글 스프레드시트 CSV 링크 적용
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
  product_col = find_col(["제품명", "KOREAN NAME"])
  completed_col = find_col(["출고 완료", "출고완료"])
  order_date_col = find_col(["발주서 수령", "발주서", "수령일"])
  yarn_col = find_col(["yarn", "번수", "실"])

  pcs_col = find_col(["order pcs", "pcs", "수량"])
  kg_col = find_col(["order kg", "kg", "중량"])
  width_col = find_col(["cm", "폭", "규격"])

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
    df["__YEAR"] = df["__PARSED_DATE"].dt.year.fillna(0).astype(int)
    df["__MONTH"] = df["__PARSED_DATE"].dt.to_period("M").astype(str)

  if order_date_col and order_date_col in df.columns:
    df["__ORDER_DATE"] = pd.to_datetime(df[order_date_col], errors="coerce")

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
                "__YEAR",
                "__MONTH",
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
                "__YEAR",
                "__MONTH",
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
            "__YEAR",
            "__MONTH",
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
    st.subheader("📈 다차원 비교 분석 시스템")

    analysis_type = st.selectbox(
        "🔍 비교 분석 기준 선택",
        [
            "연도별 (Yearly)",
            "월별 (Monthly)",
            "대리점별 (Agency)",
            "아이템 이름별 (Product Name)",
            "YARN(PILE) 사종별 (Yarn)",
            "장수별 (PCS)",
            "Kg별 (Weight)",
            "오더 중복 횟수별 (Order Duplication/Frequency)",
        ],
    )

    summary_df = pd.DataFrame()
    chart_col = None

    if analysis_type == "연도별 (Yearly)" and "__YEAR" in df.columns:
      summary_df = (
          df[df["__YEAR"] > 0]
          .groupby("__YEAR")
          .agg(
              Orders=("__YEAR", "count"),
              Total_Pcs=("__PCS_NUM", "sum"),
              Total_Kg=("__KG_NUM", "sum"),
          )
          .reset_index()
      )
      chart_col = "__YEAR"

    elif analysis_type == "월별 (Monthly)" and "__MONTH" in df.columns:
      summary_df = (
          df[df["__MONTH"] != ""]
          .groupby("__MONTH")
          .agg(
              Orders=("__MONTH", "count"),
              Total_Pcs=("__PCS_NUM", "sum"),
              Total_Kg=("__KG_NUM", "sum"),
          )
          .reset_index()
      )
      chart_col = "__MONTH"

    elif analysis_type == "대리점별 (Agency)" and agency_col in df.columns:
      summary_df = (
          df.groupby(agency_col)
          .agg(
              Orders=(agency_col, "count"),
              Total_Pcs=("__PCS_NUM", "sum"),
              Total_Kg=("__KG_NUM", "sum"),
          )
          .reset_index()
          .sort_values(by="Orders", ascending=False)
      )
      chart_col = agency_col

    elif (
        analysis_type == "아이템 이름별 (Product Name)"
        and product_col in df.columns
    ):
      summary_df = (
          df.groupby(product_col)
          .agg(
              Orders=(product_col, "count"),
              Total_Pcs=("__PCS_NUM", "sum"),
              Total_Kg=("__KG_NUM", "sum"),
          )
          .reset_index()
          .sort_values(by="Orders", ascending=False)
      )
      chart_col = product_col

    elif analysis_type == "YARN(PILE) 사종별 (Yarn)" and yarn_col in df.columns:
      summary_df = (
          df.groupby(yarn_col)
          .agg(
              Orders=(yarn_col, "count"),
              Total_Pcs=("__PCS_NUM", "sum"),
              Total_Kg=("__KG_NUM", "sum"),
          )
          .reset_index()
          .sort_values(by="Orders", ascending=False)
      )
      chart_col = yarn_col

    elif analysis_type == "장수별 (PCS)" and "__PCS_NUM" in df.columns:
      summary_df = (
          df.groupby("__PCS_NUM")
          .agg(
              Orders=("__PCS_NUM", "count"), Total_Kg=("__KG_NUM", "sum")
          )
          .reset_index()
          .sort_values(by="Orders", ascending=False)
      )
      chart_col = "__PCS_NUM"

    elif analysis_type == "Kg별 (Weight)" and "__KG_NUM" in df.columns:
      summary_df = (
          df.groupby("__KG_NUM")
          .agg(
              Orders=("__KG_NUM", "count"), Total_Pcs=("__PCS_NUM", "sum")
          )
          .reset_index()
          .sort_values(by="Orders", ascending=False)
      )
      chart_col = "__KG_NUM"

    elif (
        analysis_type == "오더 중복 횟수별 (Order Duplication/Frequency)"
        and product_col in df.columns
    ):
      summary_df = (
          df.groupby(product_col)
          .size()
          .reset_index(name="중복주문횟수")
          .sort_values(by="중복주문횟수", ascending=False)
      )
      chart_col = product_col

    if not summary_df.empty:
      st.dataframe(summary_df, use_container_width=True)

      if chart_col and chart_col in summary_df.columns:
        try:
          st.bar_chart(
              summary_df.set_index(chart_col)[
                  "Orders"
                  if "Orders" in summary_df.columns
                  else summary_df.columns[1]
              ]
          )
        except Exception:
          pass

      # 자동 코멘트(설명) 생성
      st.markdown("### 💡 분석 요약 코멘트")
      try:
        total_groups = len(summary_df)
        top_row = summary_df.iloc[0]
        top_name = top_row.iloc[0]
        top_orders = (
            top_row["Orders"] if "Orders" in summary_df.columns else "N/A"
        )
        top_kg = (
            f", 총 중량 {top_row['Total_Kg']:,.1f} Kg"
            if "Total_Kg" in summary_df.columns
            else ""
        )
        top_pcs = (
            f", 총 수량 {top_row['Total_Pcs']:,.0f} PCS"
            if "Total_Pcs" in summary_df.columns
            else ""
        )
        top_freq = (
            f", 중복 횟수 {top_row['중복주문횟수']}회"
            if "중복주문횟수" in summary_df.columns
            else ""
        )

        comment = f"""
                > **[AI 자동 분석 리포트]**
                > - 총 **{total_groups}개**의 분류 항목으로 집계되었습니다.
                > - 선택하신 **[{analysis_type}]** 기준에서 가장 수치가 높은 상위 항목은 **'{top_name}'**입니다.
                > - 해당 항목은 오더 건수 **{top_orders}건**{top_kg}{top_pcs}{top_freq}을(를) 기록하며 가장 높은 비중을 차지하고 있습니다.
                """
        st.markdown(comment)
      except Exception:
        st.info("코멘트를 생성하는 중 오류가 발생했습니다.")
    else:
      st.warning(
          "해당 조건에 일치하는 데이터가 없거나 필요한 컬럼을 찾을 수 없습니다."
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
