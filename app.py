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
# 🔐 권한별 비밀번호 설정
# ====================================================
USER_PASSWORD = "songwol1234"  # 직원/공유용 비밀번호
ADMIN_PASSWORD = "diaksp007099"  # 관리자(본인) 전용 비밀번호

if "authenticated" not in st.session_state:
  st.session_state.authenticated = False
if "is_admin" not in st.session_state:
  st.session_state.is_admin = False

# 방문 기록 저장을 위한 세션 상태 초기화
if "visit_logs" not in st.session_state:
  st.session_state.visit_logs = []

# 새로고침 시 중복 과도 카운팅을 막기 위한 세션 체크 플래그
if "counted_this_session" not in st.session_state:
  st.session_state.counted_this_session = False

# 로그인 인증 화면
if not st.session_state.authenticated:
  st.markdown(
      "<br><br><h2 style='text-align: center;'>🔐 SCM 시스템 보안 인증</h2>",
      unsafe_allow_html=True,
  )
  col1, col2, col3 = st.columns([1, 1, 1])
  with col2:
    password_input = st.text_input(
        "접속 비밀번호를 입력하세요", type="password"
    )
    if st.button("로그인", use_container_width=True):
      now_time = datetime.now()
      if password_input == ADMIN_PASSWORD:
        st.session_state.authenticated = True
        st.session_state.is_admin = True
        role_str = "관리자"
        success_msg = "관리자 권한으로 인증되었습니다!"
      elif password_input == USER_PASSWORD:
        st.session_state.authenticated = True
        st.session_state.is_admin = False
        role_str = "일반 사용자"
        success_msg = "인증되었습니다!"
      else:
        st.error("비밀번호가 틀렸습니다.")
        st.stop()

      # 방문 기록 추가 (로그인 시점)
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
  # 이미 인증된 상태에서 페이지 새로고침 시에도 방문/새로고침 기록 자동 누적
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


# 이미지 파일들을 Base64로 인코딩
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

st.title("📦 본사 문직 제품 수주 및 출고 관리 시스템")
st.markdown(
    "구글 스프레드시트 실시간 연동 SCM 대시보드 (선택형/자동완성 필터 적용)"
)

# 구글 앱스 스크립트 웹 앱 URL 입력
web_app_url = "https://script.google.com/macros/s/AKfycby_4c8lsEFsWt66f8gu9d6q0z1dPUNJ1aLCHF7pz6M5RbjpNeykU2vbXDJZZYLoKKDL/exec"


# 캐시를 적용하여 데이터 로딩 (10분 캐싱)
@st.cache_data(ttl=600, show_spinner=False)
def load_data(url):
  response = requests.get(url)
  return response.json()


# 사이드바 설정 (관리자 여부에 따라 메뉴 다르게 표시)
st.sidebar.title("🗂️ 메뉴 네비게이션")

menu_options = ["📦 메인 SCM 대시보드", "📊 SCM 통계 분석 그래프"]
if st.session_state.is_admin:
  menu_options.append("🔒 관리자 전용 방문자 통계")

menu_choice = st.sidebar.radio("이동할 메뉴:", menu_options)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 데이터 새로고침", use_container_width=True):
  load_data.clear()
  st.sidebar.success("캐시 초기화 완료!")
  st.rerun()

# 🚪 로그아웃 버튼 추가 (사이드바 하단)
st.sidebar.markdown("---")
if st.sidebar.button("🔒 로그아웃", use_container_width=True):
  st.session_state.authenticated = False
  st.session_state.is_admin = False
  st.session_state.counted_this_session = (
      False  # 재로그인 시 카운트 되도록 초기화
  )
  st.success("로그아웃 되었습니다.")
  st.rerun()

with st.spinner("구글 시트에서 데이터를 불러오는 중입니다..."):
  try:
    data = load_data(web_app_url)

    if data and len(data) > 0:
      df = pd.DataFrame(data)

      # 1. 통화 포맷 적용 ($) - 소수점 넷째 자리(:,.4f)까지 표시
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

      # 날짜 데이터 정제 ('납기 1차' 인식)
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

      # 발주서 수령일 기준 최신순(내림차순) 정렬
      df = df.sort_values(by="발주서 수령_dt", ascending=False).reset_index(
          drop=True
      )

      # 불필요한 시스템 컬럼(4차, 5차 등) 제거
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

      # 공통으로 쓰일 컬럼명 정의
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
      if menu_choice == "📦 메인 SCM 대시보드":
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
            label=f"🟢 {latest_year}년 오더 건수", value=f"{total_ordered} 건"
        )
        col_k2.metric(
            label="🟢 출고 건수",
            value=f"{completed_count} 건",
            delta="완료",
            delta_color="normal",
        )
        col_k3.metric(
            label="🟢 미출고 건수",
            value=f"{uncompleted_count} 건",
            delta="진행중",
            delta_color="inverse",
        )

        # 2. 7일 이내 임박 출고 경고 섹션
        st.markdown("---")
        st.subheader("🚨 [긴급] 7일 이내 출고 임박 리스트")
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
                f"⚠️ 향후 7일 이내 출고 예정된 미출고 건이 총"
                f" **{len(imminent_df)}건** 있습니다!"
            )
            st.dataframe(imminent_df, use_container_width=True)
          else:
            st.success("👍 향후 7일 이내에 출고 임박한 긴급 건이 없습니다.")
        else:
          st.info("납기일 데이터를 확인할 수 없습니다.")

        # 3. 월별 출고 예정 현황 (미출고 기준)
        st.markdown("---")
        st.subheader("📅 월별 출고 예정 제품 리스트 및 건수 (미출고 기준)")
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
                  "출고 예정 월을 선택하세요", valid_months, index=0
              )
              month_idx = uncompleted_df_raw[
                  uncompleted_df_raw["출고월"] == selected_month
              ].index
              month_df = display_df.loc[
                  display_df.index.intersection(month_idx)
              ]
              st.info(
                  f"📌 [{selected_month}] 출고 예정 미출고 제품: 총"
                  f" **{len(month_df)}건**"
              )
              st.dataframe(month_df, use_container_width=True)
            else:
              st.info("예정된 월별 미출고 데이터가 없습니다.")
          else:
            st.success(
                "🎉 현재 모든 오더의 출고가 완료되어 미출고 건이 없습니다!"
            )
        else:
          st.info("월별 출고 예정 데이터를 불러올 수 없습니다.")

        # 4. 메인 상세 조건 검색
        st.markdown("---")
        st.subheader("🔍 상세 조건 검색 (원하는 단어를 선택하거나 검색하세요)")

        c1, c2, c3 = st.columns(3)
        with c1:
          sel_name = st.selectbox(
              "🏷️ 제품명 선택/검색", ["전체 선택"] + all_names, key="main_name"
          )
        with c2:
          sel_width = st.selectbox(
              "📏 폭 사이즈 선택/검색",
              ["전체 선택"] + all_widths,
              key="main_width",
          )
        with c3:
          sel_item = st.selectbox(
              "🔖 파일사종 선택/검색", ["전체 선택"] + all_items, key="main_item"
          )

        search_idx = df.index
        if sel_name and sel_name != "전체 선택":
          match_mask = (
              df[name_col[0]].astype(str).str.strip() == str(sel_name).strip()
          )
          search_idx = search_idx.intersection(df[match_mask].index)
        if sel_width and sel_width != "전체 선택":
          match_mask = (
              df[width_col[0]].astype(str).str.strip() == str(sel_width).strip()
          )
          search_idx = search_idx.intersection(df[match_mask].index)
        if sel_item and sel_item != "전체 선택":
          match_mask = (
              df[item_col[0]].astype(str).str.strip() == str(sel_item).strip()
          )
          search_idx = search_idx.intersection(df[match_mask].index)

        search_df = display_df.loc[display_df.index.intersection(search_idx)]

        st.write(f"검색 결과: 총 **{len(search_df)}건**")
        st.dataframe(search_df, use_container_width=True, height=500)

        # 5. 과거 오더 건수 폴더형식 아카이브
        st.markdown("---")
        st.subheader("📁 과거 오더 건수 아카이브 (연도별 폴더)")
        past_years = [y for y in years if y < latest_year]

        if past_years:
          folder_tabs = st.tabs(
              [str(py) + "년도 오더 폴더" for py in past_years]
          )
          for idx, py in enumerate(past_years):
            py_val = past_years[idx]
            with folder_tabs[idx]:
              p_idx = df[df["연도"] == py_val].index
              p_df = display_df.loc[display_df.index.intersection(p_idx)]
              st.info(
                  f"📂 {py_val}년도 과거 오더 내역 (총 {len(p_df)}건 출고 완료"
                  " 데이터)"
              )
              st.dataframe(p_df, use_container_width=True, height=400)
        else:
          st.info("조회 가능한 과거 연도 아카이브 데이터가 없습니다.")

      # ====================================================
      # [메뉴 2] SCM 통계 분석 그래프
      # ====================================================
      elif menu_choice == "📊 SCM 통계 분석 그래프":
        st.markdown("---")
        st.subheader("📊 조건별 맞춤형 SCM 통계 분석 대시보드")
        st.markdown(
            "원하는 조건을 선택하면 해당 조건에 맞는 **연도별/월별 통계와"
            " 건수**가 즉시 분석됩니다."
        )

        with st.expander(
            "🎯 분석 조건 상세 설정 (클릭하여 열기/닫기)", expanded=True
        ):
          sc1, sc2, sc3, sc4, sc5 = st.columns(5)
          with sc1:
            stat_agency = st.selectbox(
                "🏢 대리점 선택", ["전체 선택"] + all_agencies, key="stat_agency"
            )
          with sc2:
            stat_name = st.selectbox(
                "🏷️ 제품명 선택", ["전체 선택"] + all_names, key="stat_name"
            )
          with sc3:
            stat_width = st.selectbox(
                "📏 폭 사이즈", ["전체 선택"] + all_widths, key="stat_width"
            )
          with sc4:
            stat_item = st.selectbox(
                "🔖 파일사종 (PILE/YARN)",
                ["전체 선택"] + all_items,
                key="stat_item",
            )
          with sc5:
            stat_year = st.selectbox(
                "📅 연도 선택",
                ["전체 선택"] + [str(y) for y in years],
                key="stat_year",
            )

        stat_idx = df.index
        if stat_agency and stat_agency != "전체 선택":
          m = (
              df[agency_col[0]].astype(str).str.strip()
              == str(stat_agency).strip()
          )
          stat_idx = stat_idx.intersection(df[m].index)
        if stat_name and stat_name != "전체 선택":
          m = (
              df[name_col[0]].astype(str).str.strip()
              == str(stat_name).strip()
          )
          stat_idx = stat_idx.intersection(df[m].index)
        if stat_width and stat_width != "전체 선택":
          m = (
              df[width_col[0]].astype(str).str.strip()
              == str(stat_width).strip()
          )
          stat_idx = stat_idx.intersection(df[m].index)
        if stat_item and stat_item != "전체 선택":
          m = (
              df[item_col[0]].astype(str).str.strip()
              == str(stat_item).strip()
          )
          stat_idx = stat_idx.intersection(df[m].index)
        if stat_year and stat_year != "전체 선택":
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
            label="📊 조건 검색된 총 오더 건수",
            value=f"{f_total} 건",
            delta="조회 결과",
        )
        mc2.metric(
            label="✅ 출고 완료 건수",
            value=f"{f_completed} 건",
            delta="완료",
            delta_color="normal",
        )
        mc3.metric(
            label="⏳ 미출고 진행 건수",
            value=f"{f_uncompleted} 건",
            delta="진행중",
            delta_color="inverse",
        )
        st.markdown("---")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
          st.markdown("### 📈 연도별 수주 건수 분석")
          if not filtered_stat_df.empty:
            y_trend = (
                filtered_stat_df["연도"].dropna().value_counts().reset_index()
            )
            y_trend.columns = ["연도", "건수"]
            y_trend = y_trend.sort_values("연도")
            st.bar_chart(y_trend.set_index("연도"), color="#3b82f6")
          else:
            st.info("조건에 해당하는 연도별 데이터가 없습니다.")

        with col_g2:
          st.markdown("### 📅 월별 수주 추이 분석")
          if not filtered_stat_df.empty:
            m_trend = (
                filtered_stat_df["발주월"].dropna().value_counts().reset_index()
            )
            m_trend.columns = ["발주월", "건수"]
            m_trend = m_trend.sort_values("발주월")
            st.bar_chart(m_trend.set_index("발주월"), color="#10b981")
          else:
            st.info("조건에 해당하는 월별 데이터가 없습니다.")

        st.markdown("---")
        st.subheader("📋 조건별 상세 검색 결과 목록")
        st.dataframe(filtered_display_df, use_container_width=True, height=400)

      # ====================================================
      # [메뉴 3] 관리자 전용 방문자 통계 및 분석 (관리자만 접근 가능)
      # ====================================================
      elif menu_choice == "🔒 관리자 전용 방문자 통계":
        if st.session_state.is_admin:
          st.markdown("---")
          st.subheader("🔒 관리자 전용 시스템 접속 및 방문자 분석 대시보드")
          st.markdown(
              "이 메뉴는 관리자 계정으로 로그인한 경우에만 표시되며, 실시간"
              " 접속 및 방문 통계를 분석합니다."
          )

          logs = st.session_state.visit_logs
          total_visits = len(logs)
          today_str = datetime.now().strftime("%Y-%m-%d")
          today_visits = sum(1 for log in logs if log["날짜"] == today_str)

          # 요약 메트릭 카드
          v_col1, v_col2 = st.columns(2)
          v_col1.metric(
              label="📅 오늘 총 방문(새로고침) 횟수",
              value=f"{today_visits} 회",
              delta="오늘",
          )
          v_col2.metric(
              label="📊 누적 총 방문 횟수",
              value=f"{total_visits} 회",
              delta="전체",
          )

          st.markdown("---")

          # 방문 통계 분석 그래프 영역
          if logs:
            log_df = pd.DataFrame(logs)

            v_g1, v_g2 = st.columns(2)
            with v_g1:
              st.markdown("### 📈 일자별 방문 추이 분석")
              daily_visits = log_df["날짜"].value_counts().reset_index()
              daily_visits.columns = ["날짜", "방문횟수"]
              daily_visits = daily_visits.sort_values("날짜")
              st.bar_chart(daily_visits.set_index("날짜"), color="#8b5cf6")

            with v_g2:
              st.markdown("### ⏰ 시간대별 방문 집중도 분석")
              hourly_visits = log_df["시간대"].value_counts().reset_index()
              hourly_visits.columns = ["시간대", "방문횟수"]
              hourly_visits = hourly_visits.sort_values("시간대")
              st.bar_chart(hourly_visits.set_index("시간대"), color="#f59e0b")

          st.markdown("---")
          st.subheader("📋 상세 접속 이력 로그")
          if logs:
            log_df_sorted = pd.DataFrame(logs).sort_values(
                by="접속시간", ascending=False
            )
            st.dataframe(log_df_sorted, use_container_width=True, height=350)
          else:
            st.info("기록된 방문 로그가 없습니다.")
        else:
          st.warning("접근 권한이 없습니다.")

  except Exception as e:
    st.error(f"데이터를 불러오거나 처리하는 중 오류가 발생했습니다: {e}")
