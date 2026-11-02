from datetime import datetime, timedelta
import io
import base64
from PIL import Image
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

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

# gspread를 이용한 구글 스프레드시트 연동 설정
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/13Lp9gA3p8a_WstCQA9AyMrfzM8YTtqUpBV8Ryxzszjg/edit"


@st.cache_data(ttl=30)
def load_data():
  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  credentials_dict = dict(st.secrets["gcp_service_account"])
  creds = Credentials.from_service_account_info(
      credentials_dict, scopes=scope
  )
  client = gspread.authorize(creds)

  sheet = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
  data = sheet.get_all_values()

  df_temp = pd.DataFrame(data)

  header_row = 0
  for i in range(len(df_temp)):
    row_str = str(df_temp.iloc[i].values)
    if "출하처" in row_str or "SHIPMENT" in row_str or "제품명" in row_str:
      header_row = i
      break

  data_df = pd.DataFrame(
      df_temp.values[header_row + 1 :], columns=df_temp.iloc[header_row]
  )
  data_df.columns = data_df.columns.astype(str).str.strip()
  data_df = data_df.loc[:, data_df.columns != ""]
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

  pcs_col = find_col(["order pcs", "pcs", "수량"])
  kg_col = find_col(["order kg", "kg", "중량"])
  yarn_col = find_col(["yarn", "번수", "실"])
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

  if menu == t["menu_1"]:
    target_d7 = today + timedelta(days=7)
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
    st.subheader("Order List")
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
    st.subheader("Comparative Analysis")
    if "__YEAR" in df.columns:
      yearly_summary = (
          df[df["__YEAR"] > 0]
          .groupby("__YEAR")
          .agg({"__YEAR": "count", "__KG_NUM": "sum"})
          .rename(columns={"__YEAR": "Orders", "__KG_NUM": "Total_Kg"})
          .reset_index()
      )
      st.dataframe(yearly_summary, use_container_width=True)
      st.bar_chart(yearly_summary.set_index("__YEAR")["Orders"])
    else:
      st.warning("Year data not available.")

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
