from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (와이드 모드)
st.set_page_config(
    page_title="본사 문직 제품 수주 및 출고 관리 시스템", layout="wide"
)

# ----------------------------------------------------
# 🏢 상단 오리지널 로고 직접 나란히 배치 (크기 균형 맞춤)
# ----------------------------------------------------
try:
  logo_col1, logo_col2, _ = st.columns([1.5, 1.5, 7])
  with logo_col1:
    st.image("logo_korea.png", width=180)
  with logo_col2:
    st.image("logo_vina.png", width=210)
except Exception:
  st.warning(
      "⚠️ 'logo_korea.png' 또는 'logo_vina.png' 이미지 파일을 앱 폴더에"
      " 넣어주세요."
  )

st.title("📦 본사 문직 제품 수주 및 출고 관리 시스템")
st.markdown(
    "구글 스프레드시트 실시간 연동 SCM 대시보드 (선택형/자동완성 필터 적용)"
)

# 구글 앱스 스크립트 웹 앱 URL 입력
web_app_url = (
    "https://script.google.com/macros/s/AKfycby_4c8lsEFsWt66f8gu9d6q0z1dPUNJ1aLCHF7pz6M5RbjpNeykU2vbXDJZZYLoKKDL/exec"
)


# 캐시를 적용하여 데이터 로딩 (10분 캐싱)
@st.cache_data(ttl=600, show_spinner=False)
def load_data(url):
  response = requests.get(url)
  return response.json()


# 사이드바 설정 (메뉴 네비게이션 및 새로고침)
st.sidebar.title("🗂️ 메뉴 네비게이션")
menu_choice = st.sidebar.radio(
    "이동할 메뉴:", ["📦 메인 SCM 대시보드", "📊 SCM 통계 분석 그래프"]
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 데이터 새로고침", use_container_width=True):
  load_data.clear()
  st.sidebar.success("캐시 초기화 완료!")
  st.rerun()

with st.spinner("구글 시트에서 데이터를 불러오는 중입니다..."):
  try:
    data = load_data(web_app_url)

    if data and len(data) > 0:
      df = pd.DataFrame(data)

      # 1. 통화 포맷 적용 ($)
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
              lambda x: f"$ {x:,.2f}" if pd.notnull(x) and x > 0 else ""
          )

      # 날짜 데이터 정제
      if "발주서 수령" in df.columns:
        df["발주서 수령_dt"] = pd.to_datetime(
            df["발주서 수령"], errors="coerce"
        )
      else:
        df["발주서 수령_dt"] = pd.NaT

      delivery_col = None
      for c in df.columns:
        if "확정납기 1차" in c or "DELIVERY 1" in c:
          delivery_col = c
          break

      if delivery_col:
        df["납기_dt"] = pd.to_datetime(df[delivery_col], errors="coerce")
      else:
        df["납기_dt"] = pd.NaT

      df["연도"] = df["발주서 수령_dt"].dt.year
      years = sorted(
          [int(y) for y in df["연도"].dropna().unique()], reverse=True
      )
      latest_year = years[0] if years else 2026

      # 발주서 수령일 기준 최신순(내림차순) 정렬
      df = df.sort_values(by="발주서 수령_dt", ascending=False).reset_index(
          drop=True
      )

      # 불필요한 시스템 컬럼 제거
      cols_to_drop = [
          c
          for c in df.columns
          if "4차" in c
          or "5차" in c
          or "DELIVERY 4" in c
          or "DELIVERY 5" in c
          or c in ["발주서 수령_dt", "납기_dt", "연도", "출고월", "발주월"]
      ]
      display_df = df.drop(columns=cols_to_drop, errors="ignore")

      # 공통으로 쓰일 컬럼명 정의
      name_col = [
          c for c in df.columns if "제품명" in c or "KOREAN NAME" in c
      ]
      width_col = [c for c in df.columns if "폭" in c or "width" in c.lower()]
      item_col = [
          c
          for c in df.columns
          if "ITEM" in c
          or "아이템" in c
          or "PILE" in c
          or "YARN" in c
      ]
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

        # 1. 2026년(최근 연도) 핵심 요약 카드
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
        col_k
