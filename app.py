import base64
from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (와이드 모드)
st.set_page_config(
    page_title="본사 문직 제품 수주 및 출고 관리 시스템", layout="wide"
)

# ====================================================
# 🌐 다국어 번역 딕셔너리 정의 (한국어, 영어, 베트남어)
# ====================================================
translations = {
    "한국어": {
        "auth_title": "🔐 SCM 시스템 보안 인증",
        "pw_input": "접속 비밀번호를 입력하세요",
        "login_btn": "로그인",
        "login_success": "인증되었습니다!",
        "admin_success": "관리자 권한으로 인증되었습니다!",
        "pw_error": "비밀번호가 틀렸습니다.",
        "title": "📦 본사 문직 제품 수주 및 출고 관리 시스템",
        "subtitle": (
            "구글 스프레드시트 실시간 연동 SCM 대시보드 (선택형/자동완성 필터 적용)"
        ),
        "nav_title": "🗂️ 메뉴 네비게이션",
        "menu_main": "📦 메인 SCM 대시보드",
        "menu_stat": "📊 SCM 통계 분석 그래프",
        "menu_admin": "🔒 관리자 전용 방문자 통계",
        "refresh_btn": "🔄 데이터 새로고침",
        "refresh_msg": "캐시 초기화 완료!",
        "logout_btn": "🔒 로그아웃",
        "logout_msg": "로그아웃 되었습니다.",
        "loading": "구글 시트에서 데이터를 불러오는 중입니다...",
        "year_order": "년 오더 건수",
        "completed": "출고 건수",
        "uncompleted": "미출고 건수",
        "status_done": "완료",
        "status_prog": "진행중",
        "imminent_title": "🚨 [긴급] 7일 이내 출고 임박 리스트",
        "imminent_alert": (
            "⚠️ 향후 7일 이내 출고 예정된 미출고 건이 총 **{count}건** 있습니다!"
        ),
        "imminent_none": "👍 향후 7일 이내에 출고 임박한 긴급 건이 없습니다.",
        "new_title": "✨ [신규] 최근 7일 이내 추가된 오더 리스트",
        "new_alert": (
            "📌 최근 7일 이내 새로 접수된 신규 오더가 총 **{count}건** 있습니다."
        ),
        "new_none": "👍 최근 7일 이내에 추가된 신규 오더가 없습니다.",
        "monthly_title": "📅 월별 출고 예정 제품 리스트 및 건수 (미출고 기준)",
        "monthly_select": "출고 예정 월을 선택하세요",
        "monthly_alert": "📌 [{month}] 출고 예정 미출고 제품: 총 **{count}건**",
        "monthly_none": "예정된 월별 미출고 데이터가 없습니다.",
        "monthly_all_done": (
            "🎉 현재 모든 오더의 출고가 완료되어 미출고 건이 없습니다!"
        ),
        "search_title": "🔍 상세 조건 검색 (원하는 단어를 선택하거나 검색하세요)",
        "search_name": "🏷️ 제품명 선택/검색",
        "search_width": "📏 폭 사이즈 선택/검색",
        "search_item": "🔖 파일사종 선택/검색",
        "search_res": "검색 결과: 총 **{count}건**",
        "archive_title": "📁 과거 오더 건수 아카이브 (연도별 폴더)",
        "archive_info": "📂 {year}년도 과거 오더 내역 (총 {count}건 출고 완료 데이터)",
        "stat_title": "📊 조건별 맞춤형 SCM 통계 분석 대시보드",
        "stat_sub": (
            "원하는 조건을 선택하면 해당 조건에 맞는 **연도별/월별 통계와"
            " 건수**가 즉시 분석됩니다."
        ),
        "stat_expand": "🎯 분석 조건 상세 설정 (클릭하여 열기/닫기)",
        "filter_agency": "🏢 대리점 선택",
        "filter_name": "🏷️ 제품명 선택",
        "filter_width": "📏 폭 사이즈",
        "filter_item": "🔖 파일사종 (PILE/YARN)",
        "filter_year": "📅 연도 선택",
        "stat_total": "📊 조건 검색된 총 오더 건수",
        "stat_done": "✅ 출고 완료 건수",
        "stat_prog": "⏳ 미출고 진행 건수",
        "chart_year": "📈 연도별 수수(수주) 건수 분석",
        "chart_month": "📅 월별 수주 추이 분석",
        "insight_year": "💡 **[연도별 SCM 인사이트]**",
        "insight_month": "💡 **[월별 SCM 인사이트]**",
        "table_res": "📋 조건별 상세 검색 결과 목록",
        "admin_title": "🔒 관리자 전용 시스템 접속 및 방문자 분석 대시보드",
        "admin_sub": (
            "이 메뉴는 관리자 계정으로 로그인한 경우에만 표시되며, 실시간"
            " 접속 및 방문 통계를 분석합니다."
        ),
        "today_visit": "📅 오늘 총 방문(새로고침) 횟수",
        "total_visit": "📊 누적 총 방문 횟수",
        "chart_daily": "📈 일자별 방문 추이 분석",
        "chart_hour": "⏰ 시간대별 방문 집중도 분석",
        "log_title": "📋 상세 접속 이력 로그",
        "no_log": "기록된 방문 로그가 없습니다.",
        "no_auth": "접근 권한이 없습니다.",
        "all_select": "전체 선택",
    },
    "English": {
        "auth_title": "🔐 SCM System Security Authentication",
        "pw_input": "Enter access password",
        "login_btn": "Login",
        "login_success": "Authenticated successfully!",
        "admin_success": "Authenticated with Administrator privileges!",
        "pw_error": "Incorrect password.",
        "title": "📦 Headquarters Woven Fabric Order & Delivery System",
        "subtitle": (
            "Real-time Google Sheets SCM Dashboard (Filters applied)"
        ),
        "nav_title": "🗂️ Menu Navigation",
        "menu_main": "📦 Main SCM Dashboard",
        "menu_stat": "📊 SCM Statistical Analysis",
        "menu_admin": "🔒 Admin Visitor Statistics",
        "refresh_btn": "🔄 Refresh Data",
        "refresh_msg": "Cache cleared successfully!",
        "logout_btn": "🔒 Logout",
        "logout_msg": "Logged out successfully.",
        "loading": "Loading data from Google Sheets...",
        "year_order": "Yearly Orders",
        "completed": "Completed",
        "uncompleted": "Pending",
        "status_done": "Done",
        "status_prog": "In Progress",
        "imminent_title": "🚨 [URGENT] Imminent Deliveries (Within 7 Days)",
        "imminent_alert": (
            "⚠️ There are a total of **{count}** pending orders due within 7"
            " days!"
        ),
        "imminent_none": "👍 No urgent deliveries due within the next 7 days.",
        "new_title": "✨ [NEW] Orders Received in the Last 7 Days",
        "new_alert": (
            "📌 A total of **{count}** new orders received in the last 7"
            " days."
        ),
        "new_none": "👍 No new orders received in the last 7 days.",
        "monthly_title": "📅 Monthly Scheduled Deliveries (Pending Basis)",
        "monthly_select": "Select delivery month",
        "monthly_alert": (
            "📌 [{month}] Scheduled Pending Products: Total **{count}**"
        ),
        "monthly_none": "No scheduled pending data for this month.",
        "monthly_all_done": "🎉 All orders have been completed!",
        "search_title": "🔍 Detailed Condition Search",
        "search_name": "🏷️ Product Name",
        "search_width": "📏 Width Size",
        "search_item": "🔖 Pile/Yarn Type",
        "search_res": "Search Results: Total **{count}**",
        "archive_title": "📁 Past Orders Archive (By Year)",
        "archive_info": "📂 {year} Past Orders (Total {count} completed)",
        "stat_title": "📊 Customized SCM Statistical Dashboard",
        "stat_sub": (
            "Select criteria to instantly analyze yearly/monthly statistics"
            " and counts."
        ),
        "stat_expand": "🎯 Detailed Filter Settings (Click to open/close)",
        "filter_agency": "🏢 Agency",
        "filter_name": "🏷️ Product Name",
        "filter_width": "📏 Width",
        "filter_item": "🔖 Pile/Yarn",
        "filter_year": "📅 Year",
        "stat_total": "📊 Total Filtered Orders",
        "stat_done": "✅ Completed Orders",
        "stat_prog": "⏳ Pending Orders",
        "chart_year": "📈 Yearly Order Trend Analysis",
        "chart_month": "📅 Monthly Order Trend Analysis",
        "insight_year": "💡 **[Yearly SCM Insights]**",
        "insight_month": "💡 **[Monthly SCM Insights]**",
        "table_res": "📋 Filtered Detailed Results List",
        "admin_title": "🔒 Admin Visitor Statistics & Analytics Dashboard",
        "admin_sub": (
            "This menu is only visible to administrators for real-time traffic"
            " analysis."
        ),
        "today_visit": "📅 Today's Visits (Refreshes)",
        "total_visit": "📊 Cumulative Total Visits",
        "chart_daily": "📈 Daily Visit Trend",
        "chart_hour": "⏰ Hourly Visit Concentration",
        "log_title": "📋 Detailed Access Log History",
        "no_log": "No visit logs recorded yet.",
        "no_auth": "Access denied.",
        "all_select": "Select All",
    },
    "Tiếng Việt": {
        "auth_title": "🔐 Xác thực bảo mật hệ thống SCM",
        "pw_input": "Nhập mật khẩu truy cập",
        "login_btn": "Đăng nhập",
        "login_success": "Xác thực thành công!",
        "admin_success": "Đã xác thực với quyền Quản trị viên!",
        "pw_error": "Mật khẩu không chính xác.",
        "title": "📦 Hệ thống Quản lý Đơn hàng & Giao hàng Trụ sở chính",
        "subtitle": (
            "Bảng điều khiển SCM Google Sheets thời gian thực (Đã áp dụng bộ"
            " lọc)"
        ),
        "nav_title": "🗂️ Điều hướng Menu",
        "menu_main": "📦 Bảng điều khiển SCM chính",
        "menu_stat": "📊 Phân tích thống kê SCM",
        "menu_admin": "🔒 Thống kê truy cập (Quản trị)",
        "refresh_btn": "🔄 Làm mới dữ liệu",
        "refresh_msg": "Đã xóa bộ nhớ đệm!",
        "logout_btn": "🔒 Đăng xuất",
        "logout_msg": "Đã đăng xuất thành công.",
        "loading": "Đang tải dữ liệu từ Google Sheets...",
        "year_order": "Đơn hàng trong năm",
        "completed": "Đã giao",
        "uncompleted": "Chưa giao",
        "status_done": "Hoàn thành",
        "status_prog": "Đang xử lý",
        "imminent_title": "🚨 [KHẨN CẤP] Giao hàng sắp tới trong vòng 7 ngày",
        "imminent_alert": (
            "⚠️ Có tổng số **{count}** đơn hàng chưa giao đến hạn trong 7 ngày"
            " tới!"
        ),
        "imminent_none": "👍 Không có đơn hàng khẩn cấp nào trong 7 ngày tới.",
        "new_title": "✨ [MỚI] Đơn hàng được thêm trong 7 ngày qua",
        "new_alert": (
            "📌 Tổng số **{count}** đơn hàng mới được tiếp nhận trong 7 ngày"
            " qua."
        ),
        "new_none": "👍 Không có đơn hàng mới nào trong 7 ngày qua.",
        "monthly_title": "📅 Danh sách sản phẩm dự kiến giao hàng hàng tháng",
        "monthly_select": "Chọn tháng giao hàng dự kiến",
        "monthly_alert": (
            "📌 [{month}] Sản phẩm chưa giao dự kiến: Tổng số **{count}**"
        ),
        "monthly_none": "Không có dữ liệu giao hàng chưa hoàn thành trong tháng.",
        "monthly_all_done": "🎉 Tất cả các đơn hàng đã được giao xong!",
        "search_title": "🔍 Tìm kiếm theo điều kiện chi tiết",
        "search_name": "🏷️ Tên sản phẩm",
        "search_width": "📏 Kích thước rộng",
        "search_item": "🔖 Loại sợi/Pile",
        "search_res": "Kết quả tìm kiếm: Tổng số **{count}**",
        "archive_title": "📁 Lưu trữ đơn hàng cũ (Theo năm)",
        "archive_info": "📂 Lịch sử đơn hàng năm {year} (Tổng {count} đã xong)",
        "stat_title": "📊 Bảng điều khiển Phân tích Thống kê SCM",
        "stat_sub": (
            "Chọn điều kiện để phân tích ngay lập tức thống kê và số lượng theo"
            " năm/tháng."
        ),
        "stat_expand": "🎯 Cài đặt bộ lọc chi tiết (Bấm để mở/đóng)",
        "filter_agency": "🏢 Chọn đại lý",
        "filter_name": "🏷️ Tên sản phẩm",
        "filter_width": "📏 Khổ rộng",
        "filter_item": "🔖 Loại sợi (PILE/YARN)",
        "filter_year": "📅 Chọn năm",
        "stat_total": "📊 Tổng đơn hàng tìm kiếm",
        "stat_done": "✅ Đơn hàng đã giao",
        "stat_prog": "⏳ Đơn hàng đang xử lý",
        "chart_year": "📈 Phân tích xu hướng đơn hàng theo năm",
        "chart_month": "📅 Phân tích xu hướng đơn hàng theo tháng",
        "insight_year": "💡 **[Thông tin chi tiết SCM theo năm]**",
        "insight_month": "💡 **[Thông tin chi tiết SCM theo tháng]**",
        "table_res": "📋 Danh sách kết quả tìm kiếm chi tiết",
        "admin_title": "🔒 Bảng điều khiển Phân tích & Thống kê Quản trị viên",
        "admin_sub": (
            "Menu này chỉ hiển thị khi đăng nhập tài khoản Quản trị viên."
        ),
        "today_visit": "📅 Tổng lượt truy cập hôm nay",
        "total_visit": "📊 Tổng lượt truy cập tích lũy",
        "chart_daily": "📈 Xu hướng truy cập theo ngày",
        "chart_hour": "⏰ Mật độ truy cập theo khung giờ",
        "log_title": "📋 Nhật ký lịch sử truy cập chi tiết",
        "no_log": "Chưa có nhật ký truy cập nào.",
        "no_auth": "Không có quyền truy cập.",
        "all_select": "Chọn tất cả",
    },
}

# 사이드바 상단에 언어 선택 셀렉트박스 배치
selected_lang = st.sidebar.selectbox(
    "🌐 언어 / Language / Ngôn ngữ", ["한국어", "English", "Tiếng Việt"]
)
dict_t = translations[selected_lang]


# ====================================================
# 🔐 권한별 비밀번호 설정
# ====================================================
USER_PASSWORD = "songwol1234"  # 직원/공유용 비밀번호
ADMIN_PASSWORD = "diaksp007099"  # 관리자(본인) 전용 비밀번호

if "authenticated" not in st.session_state:
  st.session_state.authenticated = False
if "is_admin" not in st.session_state:
  st.session_state.is_admin = False

if "visit_logs" not in st.session_state:
  st.session_state.visit_logs = []
if "counted_this_session" not in st.session_state:
  st.session_state.counted_this_session = False

# 로그인 인증 화면
if not st.session_state.authenticated:
  st.markdown(
      f"<br><br><h2 style='text-align: center;'>{dict_t['auth_title']}</h2>",
      unsafe_allow_html=True,
  )
  col1, col2, col3 = st.columns([1, 1, 1])
  with col2:
    password_input = st.text_input(dict_t["pw_input"], type="password")
    if st.button(dict_t["login_btn"], use_container_width=True):
      now_time = datetime.now()
      if password_input == ADMIN_PASSWORD:
        st.session_state.authenticated = True
        st.session_state.is_admin = True
        role_str = "관리자"
        success_msg = dict_t["admin_success"]
      elif password_input == USER_PASSWORD:
        st.session_state.authenticated = True
        st.session_state.is_admin = False
        role_str = "일반 사용자"
        success_msg = dict_t["login_success"]
      else:
        st.error(dict_t["pw_error"])
        st.stop()

      if not st.session_state.counted_this_session:
        st.session_state.visit_logs.append({
            "접속시간": now_time.strftime("%Y-%m-%d %H:%M:%S"),
            "날짜": now_time.strftime("%Y-%m-%d"),
            "시간대": now_time.strftime("%H시"),
            "권한": role_str,
        })
        st.session_state.counted_this_session = True

      st.success(success_msg)
      st.rerun()
  st.stop()
else:
  if not st.session_state.counted_this_session:
    now_time = datetime.now()
    role_str = "관리자" if st.session_state.is_admin else "일반 사용자"
    st.session_state.visit_logs.append({
        "접속시간": now_time.strftime("%Y-%m-%d %H:%M:%S"),
        "날짜": now_time.strftime("%Y-%m-%d"),
        "시간대": now_time.strftime("%H시"),
        "권한": role_str,
    })
    st.session_state.counted_this_session = True


# 로컬 이미지 파일을 Base64로 변환하여 HTML에서 깨지지 않도록 처리하는 함수
def get_base64_image(image_path):
  try:
    with open(image_path, "rb") as f:
      data = f.read()
    return base64.b64encode(data).decode()
  except Exception:
    return ""


img_korea_base64 = get_base64_image("logo_korea.png")
img_vina_base64 = get_base64_image("logo_vina.png")

# ----------------------------------------------------
# 🏢 상단 오리지널 로고 나란히 배치 및 정렬(ALIGN) 최적화
# ----------------------------------------------------
st.markdown(
    f"""
    <style>
    .brand-logo-wrapper {{
        display: flex;
        align-items: center;
        gap: 25px;
        margin-bottom: 12px;
        padding-top: 5px;
    }}
    .brand-logo-wrapper img {{
        height: 38px;
        object-fit: contain;
    }}
    </style>
    <div class="brand-logo-wrapper">
        <img src="data:image/png;base64,{img_korea_base64}" alt="SONGWOL KOREA">
        <img src="data:image/png;base64,{img_vina_base64}" alt="SONGWOL VINA">
    </div>
""",
    unsafe_allow_html=True,
)

st.title(dict_t["title"])
st.markdown(dict_t["subtitle"])

# 구글 앱스 스크립트 웹 앱 URL 입력
web_app_url = "https://script.google.com/macros/s/AKfycby_4c8lsEFsWt66f8gu9d6q0z1dPUNJ1aLCHF7pz6M5RbjpNeykU2vbXDJZZYLoKKDL/exec"


# 캐시를 적용하여 데이터 로딩 (10분 캐싱)
@st.cache_data(ttl=600, show_spinner=False)
def load_data(url):
  response = requests.get(url)
  return response.json()


# 사이드바 설정
st.sidebar.title(dict_t["nav_title"])

menu_options = [dict_t["menu_main"], dict_t["menu_stat"]]
if st.session_state.is_admin:
  menu_options.append(dict_t["menu_admin"])

menu_choice = st.sidebar.radio("이동할 메뉴:", menu_options)

st.sidebar.markdown("---")
if st.sidebar.button(dict_t["refresh_btn"], use_container_width=True):
  load_data.clear()
  st.sidebar.success(dict_t["refresh_msg"])
  st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button(dict_t["logout_btn"], use_container_width=True):
  st.session_state.authenticated = False
  st.session_state.is_admin = False
  st.session_state.counted_this_session = False
  st.success(dict_t["logout_msg"])
  st.rerun()

with st.spinner(dict_t["loading"]):
  try:
    data = load_data(web_app_url)

    if data and len(data) > 0:
      df = pd.DataFrame(data)

      for col in df.columns:
        if "단가" in col or "총액" in col or "AMOUNT" in col or "FOB" in col:
          df[col] = pd.to_numeric(
              df[col]
              .astype(str)
              .str.replace("$", "", regex=False)
              .str.replace(",", "", regex=False)
              .str.strip(),
              errors="coerce",
          )
          df[col] = df[col].apply(
              lambda x: f"$ {x:,.4f}" if pd.notnull(x) and x > 0 else ""
          )

      if "발주서 수령" in df.columns:
        df["발주서 수령_dt"] = pd.to_datetime(
            df["발주서 수령"], errors="coerce"
        )
      else:
        df["발주서 수령_dt"] = pd.NaT

      delivery_col = None
      for c in df.columns:
        if "납기 1차" in c or "확정납기 1차" in c or "DELIVERY 1" in c:
          delivery_col = c
          break

      if delivery_col:
        df["납기_dt"] = pd.to_datetime(df[delivery_col], errors="coerce")
      else:
        df["납기_dt"] = pd.NaT

      df["연도"] = df["발주서 수령_dt"].dt.year
      df["발주월"] = df["발주서 수령_dt"].dt.strftime("%Y-%m")
      years = sorted(
          [int(y) for y in df["연도"].dropna().unique()], reverse=True
      )
      latest_year = years[0] if years else 2026

      df = df.sort_values(by="발주서 수령_dt", ascending=False).reset_index(
          drop=True
      )

      cols_to_drop = [
          c
          for c in df.columns
          if "4차" in c
          or "5차" in c
          or "DELIVERY 4" in c
          or "DELIVERY 5" in c
          or c in ["발주서 수령_dt", "납기_dt"]
      ]
      display_df = df.drop(columns=cols_to_drop, errors="ignore")

      name_col = [c for c in df.columns if "제품명" in c or "KOREAN NAME" in c]
      width_col = [c for c in df.columns if "폭" in c or "width" in c.lower()]
      item_col = [c for c in df.columns if "PILE" in c or "YARN" in c]
      agency_col = [c for c in df.columns if "대리점" in c or "AGENCY" in c]

      all_names = (
          sorted(
              [
                  str(x)
                  for x in df[name_col[0]].dropna().unique()
                  if str(x).strip() != ""
              ]
          )
          if name_col
          else []
      )
      all_widths = (
          sorted(
              [
                  str(x)
                  for x in df[width_col[0]].dropna().unique()
                  if str(x).strip() != ""
              ],
              key=lambda x: float(x)
              if x.replace(".", "", 1).isdigit()
              else 0,
          )
          if width_col
          else []
      )
      all_items = (
          sorted(
              [
                  str(x)
                  for x in df[item_col[0]].dropna().unique()
                  if str(x).strip() != ""
              ]
          )
          if item_col
          else []
      )
      all_agencies = (
          sorted(
              [
                  str(x)
                  for x in df[agency_col[0]].dropna().unique()
                  if str(x).strip() != ""
              ]
          )
          if agency_col
          else []
      )

      # ====================================================
      # [메뉴 1] 메인 SCM 대시보드
      # ====================================================
      if menu_choice == dict_t["menu_main"]:
        st.markdown("---")
        latest_df_raw = df[df["연도"] == latest_year]
        total_ordered = len(latest_df_raw)
        completed_count = len(
            latest_df_raw[
                latest_df_raw["출고 완료"].astype(str).str.upper() == "O"
            ]
        )
        uncompleted_count = total_ordered - completed_count

        col_k1, col_k2, col_k3 = st.columns(3)
        col_k1.metric(
            label=f"🟢 {latest_year} {dict_t['year_order']}",
            value=f"{total_ordered} 건",
        )
        col_k2.metric(
            label=f"🟢 {dict_t['completed']}",
            value=f"{completed_count} 건",
            delta=dict_t["status_done"],
            delta_color="normal",
        )
        col_k3.metric(
            label=f"🟢 {dict_t['uncompleted']}",
            value=f"{uncompleted_count} 건",
            delta=dict_t["status_prog"],
            delta_color="inverse",
        )

        # 1. [긴급] 7일 이내 출고 임박 리스트
        st.markdown("---")
        st.subheader(dict_t["imminent_title"])
        today = datetime.now()
        seven_days_later = today + timedelta(days=7)

        if delivery_col and not df["납기_dt"].isna().all():
          not_completed_mask = df["출고 완료"].astype(str).str.upper() != "O"
          date_mask = (df["납기_dt"] >= today - timedelta(days=1)) & (
              df["납기_dt"] <= seven_days_later
          )
          imminent_idx = df[not_completed_mask & date_mask].index
          imminent_df = display_df.loc[
              display_df.index.intersection(imminent_idx)
          ]

          if not imminent_df.empty:
            st.error(
                dict_t["imminent_alert"].format(count=len(imminent_df))
            )
            st.dataframe(imminent_df, use_container_width=True)
          else:
            st.success(dict_t["imminent_none"])
        else:
          st.info("납기일 데이터를 확인할 수 없습니다.")

        # 2. ✨ [신규] 최근 7일 이내 추가된 신규 오더 리스트
        st.markdown("---")
        st.subheader(dict_t["new_title"])

        if not df["발주서 수령_dt"].isna().all():
          seven_days_ago = today - timedelta(days=7)
          new_order_mask = df["발주서 수령_dt"] >= seven_days_ago
          new_order_idx = df[new_order_mask].index
          new_order_df = display_df.loc[
              display_df.index.intersection(new_order_idx)
          ]

          if not new_order_df.empty:
            st.info(dict_t["new_alert"].format(count=len(new_order_df)))
            st.dataframe(new_order_df, use_container_width=True)
          else:
            st.success(dict_t["new_none"])
        else:
          st.info("발주서 수령일 데이터를 확인할 수 없습니다.")

        # 3. 월별 출고 예정 현황 (미출고 기준)
        st.markdown("---")
        st.subheader(dict_t["monthly_title"])
        if delivery_col and not df["납기_dt"].isna().all():
          uncompleted_df_raw = df[
              df["출고 완료"].astype(str).str.upper() != "O"
          ].copy()

          if not uncompleted_df_raw.empty:
            uncompleted_df_raw["출고월"] = (
                uncompleted_df_raw["납기_dt"].dt.strftime("%Y-%m")
            )
            valid_months = (
                uncompleted_df_raw[
                    uncompleted_df_raw["출고월"].notnull()
                    & (uncompleted_df_raw["출고월"] != "NaT")
                ]
                .sort_values("출고월", ascending=True)["출고월"]
                .unique()
            )

            if len(valid_months) > 0:
              selected_month = st.selectbox(
                  dict_t["monthly_select"], valid_months, index=0
              )
              month_idx = uncompleted_df_raw[
                  uncompleted_df_raw["출고월"] == selected_month
              ].index
              month_df = display_df.loc[
                  display_df.index.intersection(month_idx)
              ]
              st.info(
                  dict_t["monthly_alert"].format(
                      month=selected_month, count=len(month_df)
                  )
              )
              st.dataframe(month_df, use_container_width=True)
            else:
              st.info(dict_t["monthly_none"])
          else:
            st.success(dict_t["monthly_all_done"])
        else:
          st.info("월별 출고 예정 데이터를 불러올 수 없습니다.")

        # 4. 메인 상세 조건 검색
        st.markdown("---")
        st.subheader(dict_t["search_title"])

        c1, c2, c3 = st.columns(3)
        with c1:
          sel_name = st.selectbox(
              dict_t["search_name"],
              [dict_t["all_select"]] + all_names,
              key="main_name",
          )
        with c2:
          sel_width = st.selectbox(
              dict_t["search_width"],
              [dict_t["all_select"]] + all_widths,
              key="main_width",
          )
        with c3:
          sel_item = st.selectbox(
              dict_t["search_item"],
              [dict_t["all_select"]] + all_items,
              key="main_item",
          )

        search_idx = df.index
        if sel_name and sel_name != dict_t["all_select"]:
          match_mask = (
              df[name_col[0]].astype(str).str.strip() == str(sel_name).strip()
          )
          search_idx = search_idx.intersection(df[match_mask].index)
        if sel_width and sel_width != dict_t["all_select"]:
          match_mask = (
              df[width_col[0]].astype(str).str.strip() == str(sel_width).strip()
          )
          search_idx = search_idx.intersection(df[match_mask].index)
        if sel_item and sel_item != dict_t["all_select"]:
          match_mask = (
              df[item_col[0]].astype(str).str.strip() == str(sel_item).strip()
          )
          search_idx = search_idx.intersection(df[match_mask].index)

        search_df = display_df.loc[display_df.index.intersection(search_idx)]

        st.write(dict_t["search_res"].format(count=len(search_df)))
        st.dataframe(search_df, use_container_width=True, height=500)

        # 5. 과거 오더 건수 폴더형식 아카이브
        st.markdown("---")
        st.subheader(dict_t["archive_title"])
        past_years = [y for y in years if y < latest_year]

        if past_years:
          folder_tabs = st.tabs(
              [str(py) + ("년도" if selected_lang == "한국어" else " Year") for py in past_years]
          )
          for idx, py in enumerate(past_years):
            py_val = past_years[idx]
            with folder_tabs[idx]:
              p_idx = df[df["연도"] == py_val].index
              p_df = display_df.loc[display_df.index.intersection(p_idx)]
              st.info(dict_t["archive_info"].format(year=py_val, count=len(p_df)))
              st.dataframe(p_df, use_container_width=True, height=400)
        else:
          st.info("조회 가능한 과거 연도 아카이브 데이터가 없습니다.")

      # ====================================================
      # [메뉴 2] SCM 통계 분석 그래프
      # ====================================================
      elif menu_choice == dict_t["menu_stat"]:
        st.markdown("---")
        st.subheader(dict_t["stat_title"])
        st.markdown(dict_t["stat_sub"])

        with st.expander(dict_t["stat_expand"], expanded=True):
          sc1, sc2, sc3, sc4, sc5 = st.columns(5)
          with sc1:
            stat_agency = st.selectbox(
                dict_t["filter_agency"],
                [dict_t["all_select"]] + all_agencies,
                key="stat_agency",
            )
          with sc2:
            stat_name = st.selectbox(
                dict_t["filter_name"],
                [dict_t["all_select"]] + all_names,
                key="stat_name",
            )
          with sc3:
            stat_width = st.selectbox(
                dict_t["filter_width"],
                [dict_t["all_select"]] + all_widths,
                key="stat_width",
            )
          with sc4:
            stat_item = st.selectbox(
                dict_t["filter_item"],
                [dict_t["all_select"]] + all_items,
                key="stat_item",
            )
          with sc5:
            stat_year = st.selectbox(
                dict_t["filter_year"],
                [dict_t["all_select"]] + [str(y) for y in years],
                key="stat_year",
            )

        stat_idx = df.index
        if stat_agency and stat_agency != dict_t["all_select"]:
          m = (
              df[agency_col[0]].astype(str).str.strip()
              == str(stat_agency).strip()
          )
          stat_idx = stat_idx.intersection(df[m].index)
        if stat_name and stat_name != dict_t["all_select"]:
          m = (
              df[name_col[0]].astype(str).str.strip()
              == str(stat_name).strip()
          )
          stat_idx = stat_idx.intersection(df[m].index)
        if stat_width and stat_width != dict_t["all_select"]:
          m = (
              df[width_col[0]].astype(str).str.strip()
              == str(stat_width).strip()
          )
          stat_idx = stat_idx.intersection(df[m].index)
        if stat_item and stat_item != dict_t["all_select"]:
          m = (
              df[item_col[0]].astype(str).str.strip()
              == str(stat_item).strip()
          )
          stat_idx = stat_idx.intersection(df[m].index)
        if stat_year and stat_year != dict_t["all_select"]:
          m = df["연도"].astype(str) == str(stat_year)
          stat_idx = stat_idx.intersection(df[m].index)

        filtered_stat_df = df.loc[df.index.intersection(stat_idx)]
        filtered_display_df = display_df.loc[
            display_df.index.intersection(stat_idx)
        ]

        st.markdown("---")
        f_total = len(filtered_stat_df)
        f_completed = len(
            filtered_stat_df[
                filtered_stat_df["출고 완료"].astype(str).str.upper() == "O"
            ]
        )
        f_uncompleted = f_total - f_completed

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric(
            label=dict_t["stat_total"],
            value=f"{f_total} 건",
            delta="조회 결과",
        )
        mc2.metric(
            label=dict_t["stat_done"],
            value=f"{f_completed} 건",
            delta=dict_t["status_done"],
            delta_color="normal",
        )
        mc3.metric(
            label=dict_t["stat_prog"],
            value=f"{f_uncompleted} 건",
            delta=dict_t["status_prog"],
            delta_color="inverse",
        )
        st.markdown("---")

        col_g1, col_g2 = st.columns(2)

        with col_g1:
          st.markdown(f"### {dict_t['chart_year']}")
          if not filtered_stat_df.empty:
            y_trend = (
                filtered_stat_df["연도"].dropna().value_counts().reset_index()
            )
            y_trend.columns = ["연도", "건수"]
            y_trend = y_trend.sort_values("연도")
            st.bar_chart(y_trend.set_index("연도"), color="#3b82f6")

            if len(y_trend) >= 2:
              latest_row = y_trend.iloc[-1]
              prev_row = y_trend.iloc[-2]
              cur_year = latest_row["연도"]
              cur_cnt = latest_row["건수"]
              prev_year = prev_row["연도"]
              prev_cnt = prev_row["건수"]

              if prev_cnt > 0:
                diff_pct = ((cur_cnt - prev_cnt) / prev_cnt) * 100
                direction = "증가" if diff_pct >= 0 else "감소"
                st.info(
                    f"{dict_t['insight_year']}\n\n- 직전 연도인"
                    f" **{prev_year}년({prev_cnt}건)** 대비 **{cur_year}년"
                    f" ({cur_cnt}건)** 기준 수주량이 **{abs(diff_pct):.1f}%"
                    f" {direction}** 추세를 보이고 있습니다."
                )
            else:
              st.info("비교할 수 있는 이전 연도 데이터가 부족합니다.")
          else:
            st.info("조건에 해당하는 연도별 데이터가 없습니다.")

        with col_g2:
          st.markdown(f"### {dict_t['chart_month']}")
          if not filtered_stat_df.empty:
            m_trend = (
                filtered_stat_df["발주월"].dropna().value_counts().reset_index()
            )
            m_trend.columns = ["발주월", "건수"]
            m_trend = m_trend.sort_values("발주월")
            st.bar_chart(m_trend.set_index("발주월"), color="#10b981")

            if not m_trend.empty:
              max_month_row = m_trend.loc[m_trend["건수"].idxmax()]
              peak_month = max_month_row["발주월"]
              peak_cnt = max_month_row["건수"]
              avg_cnt = m_trend["건수"].mean()

              st.info(
                  f"{dict_t['insight_month']}\n\n- 분석 기간 중 가장 수주가"
                  f" 집중된 피크(Peak) 시기는 **{peak_month}**이며, 총"
                  f" **{peak_cnt}건**의 오더가 집중되었습니다. (월평균 약"
                  f" {avg_cnt:.1f}건)"
              )
            else:
              st.info("월별 트렌드를 분석할 데이터가 부족합니다.")
          else:
            st.info("조건에 해당하는 월별 데이터가 없습니다.")

        st.markdown("---")
        st.subheader(dict_t["table_res"])
        st.dataframe(filtered_display_df, use_container_width=True, height=400)

      # ====================================================
      # [메뉴 3] 관리자 전용 방문자 통계 및 분석
      # ====================================================
      elif menu_choice == dict_t["menu_admin"]:
        if st.session_state.is_admin:
          st.markdown("---")
          st.subheader(dict_t["admin_title"])
          st.markdown(dict_t["admin_sub"])

          logs = st.session_state.visit_logs
          total_visits = len(logs)
          today_str = datetime.now().strftime("%Y-%m-%d")
          today_visits = sum(1 for log in logs if log["날짜"] == today_str)

          v_col1, v_col2 = st.columns(2)
          v_col1.metric(
              label=dict_t["today_visit"],
              value=f"{today_visits} 회",
              delta="오늘",
          )
          v_col2.metric(
              label=dict_t["total_visit"],
              value=f"{total_visits} 회",
              delta="전체",
          )

          st.markdown("---")

          if logs:
            log_df = pd.DataFrame(logs)

            v_g1, v_g2 = st.columns(2)
            with v_g1:
              st.markdown(f"### {dict_t['chart_daily']}")
              daily_visits = log_df["날짜"].value_counts().reset_index()
              daily_visits.columns = ["날짜", "방문횟수"]
              daily_visits = daily_visits.sort_values("날짜")
              st.bar_chart(daily_visits.set_index("날짜"), color="#8b5cf6")

            with v_g2:
              st.markdown(f"### {dict_t['chart_hour']}")
              hourly_visits = log_df["시간대"].value_counts().reset_index()
              hourly_visits.columns = ["시간대", "방문횟수"]
              hourly_visits = hourly_visits.sort_values("시간대")
              st.bar_chart(hourly_visits.set_index("시간대"), color="#f59e0b")

          st.markdown("---")
          st.subheader(dict_t["log_title"])
          if logs:
            log_df_sorted = pd.DataFrame(logs).sort_values(
                by="접속시간", ascending=False
            )
            st.dataframe(log_df_sorted, use_container_width=True, height=350)
          else:
            st.info(dict_t["no_log"])
        else:
          st.warning(dict_t["no_auth"])

  except Exception as e:
    st.error(f"데이터를 불러오거나 처리하는 중 오류가 발생했습니다: {e}")
