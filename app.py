from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (와이드 모드)
st.set_page_config(
    page_title="본사 문직 제품 수주 및 출고 관리 시스템", layout="wide"
)

st.title("📦 본사 문직 제품 수주 및 출고 관리 시스템")
st.markdown(
    "구글 스프레드시트 연동 SCM 대시보드 (임박 출고 경고, 월별 예정, 연도별"
    " 관리, 통계 그래프)"
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


# 상단 우측 [새로고침] 버튼
col1, col2 = st.columns([6, 1])
with col2:
  if st.button("🔄 새로고침", use_container_width=True):
    load_data.clear()
    st.success("캐시가 초기화되었습니다!")
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

      # 날짜 데이터 정제 (발주서 수령, 확정납기 1차 등)
      if "발주서 수령" in df.columns:
        df["발주서 수령_dt"] = pd.to_datetime(
            df["발주서 수령"], errors="coerce"
        )
      else:
        df["발주서 수령_dt"] = pd.NaT

      # 확정납기 1차 컬럼 찾기
      delivery_col = None
      for c in df.columns:
        if "확정납기 1차" in c or "DELIVERY 1" in c:
          delivery_col = c
          break

      if delivery_col:
        df["납기_dt"] = pd.to_datetime(df[delivery_col], errors="coerce")
      else:
        df["납기_dt"] = pd.NaT

      # ----------------------------------------------------
      # 🚨 기능 1: 7일 이내 임박 출고 리스트 경고 섹션
      # ----------------------------------------------------
      st.markdown("---")
      st.subheader("🚨 [긴급] 7일 이내 출고 임박 리스트")

      today = datetime.now()
      seven_days_later = today + timedelta(days=7)

      if delivery_col and not df["납기_dt"].isna().all():
        # 출고 완료가 안 되었고('O'가 아님), 납기가 오늘부터 7일 이내인 항목
        not_completed = df[df["출고 완료"].astype(str).str.upper() != "O"]
        imminent_df = not_completed[
            (not_completed["납기_dt"] >= today - timedelta(days=1))
            & (not_completed["납기_dt"] <= seven_days_later)
        ]

        if not imminent_df.empty:
          st.error(
              f"⚠️ 향후 7일 이내 출고 예정된 건이 총 **{len(imminent_df)}건**"
              " 있습니다! 확인이 필요합니다."
          )
          st.dataframe(imminent_df, use_container_width=True)
        else:
          st.success(
              "👍 향후 7일 이내에 출고 임박한 긴급 건이 없습니다."
          )
      else:
        st.info("납기일 데이터가 확인되지 않아 임박 리스트를 산출할 수 없습니다.")

      # ----------------------------------------------------
      # 📅 기능 2: 월별 출고 예정 제품 리스트 및 건수
      # ----------------------------------------------------
      st.markdown("---")
      st.subheader("📅 월별 출고 예정 현황")

      if delivery_col and not df["납기_dt"].isna().all():
        df["출고월"] = df["납기_dt"].dt.strftime("%Y-%m")
        valid_months = (
            df[df["출고월"].notnull() & (df["출고월"] != "NaT")]
            .sort_values("출고월")["출고월"]
            .unique()
        )

        if len(valid_months) > 0:
          selected_month = st.selectbox(
              "출고 예정 월을 선택하세요", valid_months
          )
          month_df = df[df["출고월"] == selected_month]
          st.info(
              f"📌 [{selected_month}] 출고 예정 제품: 총"
              f" **{len(month_df)}건**"
          )
          st.dataframe(month_df, use_container_width=True)
      else:
        st.info("월별 출고 예정 데이터를 불러올 수 없습니다.")

      # ----------------------------------------------------
      # 📊 기능 3: 가장 최근 연도 현황 요약 및 이전 연도 폴더 분리
      # ----------------------------------------------------
      st.markdown("---")
      st.subheader("📂 연도별 수주 및 출고 관리")

      df["연도"] = df["발주서 수령_dt"].dt.year
      years = sorted(
          [int(y) for y in df["연도"].dropna().unique()], reverse=True
      )

      if years:
        latest_year = years[0]  # 가장 최근 연도
        st.markdown(
            f"### 🔥 가장 최근 연도 ({latest_year}년) 핵심 요약"
        )

        latest_df = df[df["연도"] == latest_year]
        total_ordered = len(latest_df)
        completed_df = latest_df[
            latest_df["출고 완료"].astype(str).str.upper() == "O"
        ]
        total_completed = len(completed_df)
        total_remaining = total_ordered - total_completed

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric(
            label=f"{latest_year}년 총 발주 접수", value=f"{total_ordered}건"
        )
        col_m2.metric(
            label=f"{latest_year}년 출고 완료", value=f"{total_completed}건"
        )
        col_m3.metric(
            label=f"{latest_year}년 잔여(미출고)",
            value=f"{total_remaining}건",
            delta_color="inverse",
        )

        st.dataframe(latest_df, use_container_width=True, height=400)

        # 이전 연도 데이터 (폴더 개념의 탭 분리)
        past_years = years[1:]
        if past_years:
          st.markdown("### 📁 이전 연도 아카이브 폴더")
          year_tabs = st.tabs([str(y) + "년" for y in past_years])

          for idx, py in enumerate(past_years):
            with year_tabs[idx]:
              past_df = df[df["연도"] == py]
              st.write(
                  f"**{py}년도 데이터** (총 {len(past_df)}건 발주 / 수령 내역)"
              )
              st.dataframe(past_df, use_container_width=True, height=350)
      else:
        st.dataframe(df, use_container_width=True)

      # ----------------------------------------------------
      # 🔍 기능 4: 제품명, 폭사이즈, 실사종(ERP/아이템명 등) 상세 검색 기능
      # ----------------------------------------------------
      st.markdown("---")
      st.subheader("🔍 통합 다중 조건 검색 (제품명 / 폭 / 실사종 등)")

      col_s1, col_s2, col_s3 = st.columns(3)
      with col_s1:
        q_name = st.text_input("🏷️ 제품명 검색", "")
      with col_s2:
        q_width = st.text_input("📏 폭 사이즈 검색 (예: 40)", "")
      with col_s3:
        q_item = st.text_input("🔖 실사종 / ITEM 검색", "")

      search_df = df.copy()
      if q_name:
        search_df = search_df[
            search_df.astype(str)
            .apply(lambda row: row.str.contains(q_name, case=False))
            .any(axis=1)
        ]
      if q_width:
        width_col = [
            c for c in search_df.columns if "폭" in c or "width" in c.lower()
        ]
        if width_col:
          search_df = search_df[
              search_df[width_col[0]].astype(str).str.contains(q_width, case=False)
          ]
      if q_item:
        item_col = [
            c
            for c in search_df.columns
            if "ITEM" in c
            or "아이템" in c
            or "PILE" in c
            or "YARN" in c
        ]
        if item_col:
          search_df = search_df[
              search_df[item_col].astype(str).apply(
                  lambda row: row.str.contains(q_item, case=False)
              ).any(axis=1)
          ]

      st.write(f"검색 결과: 총 **{len(search_df)}건**")
      st.dataframe(search_df, use_container_width=True, height=500)

      # ----------------------------------------------------
      # 📈 기능 5: 월별 / 대리점별 통계 분석 그래프
      # ----------------------------------------------------
      st.markdown("---")
      st.subheader("📊 SCM 통계 분석 그래프")

      g_col1, g_col2 = st.columns(2)

      with g_col1:
        st.markdown("#### 📅 월별 발주 건수 추이")
        if "발주서 수령_dt" in df.columns:
          df["발주월"] = df["발주서 수령_dt"].dt.strftime("%Y-%m")
          monthly_counts = (
              df["발주월"].value_counts().sort_index().reset_index()
          )
          monthly_counts.columns = ["월", "발주건수"]
          if not monthly_counts.empty:
            st.bar_chart(monthly_counts.set_index("월"))
          else:
            st.info("데이터가 부족합니다.")

      with g_col2:
        st.markdown("#### 🏢 대리점별 발주 비중 Top 10")
        agency_col = [c for c in df.columns if "대리점" in c or "AGENCY" in c]
        if agency_col:
          agency_counts = df[agency_col[0]].value_counts().head(10)
          if not agency_counts.empty:
            st.bar_chart(agency_counts)
          else:
            st.info("대리점 데이터가 부족합니다.")

    else:
      st.warning("가져온 데이터가 비어있습니다. 시트 내용을 확인해 주세요.")

  except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
