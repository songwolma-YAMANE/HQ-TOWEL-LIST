from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (와이드 모드)
st.set_page_config(
    page_title="본사 문직 제품 수주 및 출고 관리 시스템", layout="wide"
)

st.title("📦 본사 문직 제품 수주 및 출고 관리 시스템")
st.markdown("구글 스프레드시트 실시간 연동 SCM 대시보드 (최신 출고 및 사이드바 메뉴)")

# 구글 앱스 스크립트 웹 앱 URL 입력
web_app_url = (
    "https://script.google.com/macros/s/AKfycby_4c8lsEFsWt66f8gu9d6q0z1dPUNJ1aLCHF7pz6M5RbjpNeykU2vbXDJZZYLoKKDL/exec"
)


# 캐시를 적용하여 데이터 로딩 (10분 캐싱)
@st.cache_data(ttl=600, show_spinner=False)
def load_data(url):
  response = requests.get(url)
  return response.json()


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

      # ----------------------------------------------------
      # 📂 [사이드바 메뉴] 폴더 형식 네비게이션
      # ----------------------------------------------------
      st.sidebar.title("🗂️ SCM 메뉴 폴더")
      menu_mode = st.sidebar.radio(
          "이동할 메뉴를 선택하세요:",
          [
              "📦 메인 수주/출고 관리",
              "📁 이전 연도 아카이브",
              "📊 SCM 통계 분석 그래프",
          ],
      )

      st.sidebar.markdown("---")
      if st.sidebar.button("🔄 데이터 새로고침", use_container_width=True):
        load_data.clear()
        st.sidebar.success("캐시 초기화 완료!")
        st.rerun()

      # ====================================================
      # [메뉴 1] 메인 수주/출고 관리 화면
      # ====================================================
      if menu_mode == "📦 메인 수주/출고 관리":

        # 1. 7일 이내 임박 출고 경고 섹션
        st.subheader("🚨 [긴급] 7일 이내 출고 임박 리스트")
        today = datetime.now()
        seven_days_later = today + timedelta(days=7)

        if delivery_col and not df["납기_dt"].isna().all():
          not_completed = df[df["출고 완료"].astype(str).str.upper() != "O"]
          imminent_df = not_completed[
              (not_completed["납기_dt"] >= today - timedelta(days=1))
              & (not_completed["납기_dt"] <= seven_days_later)
          ]

          if not imminent_df.empty:
            st.error(
                f"⚠️ 향후 7일 이내 출고 예정된 건이 총 **{len(imminent_df)}건**"
                " 있습니다!"
            )
            st.dataframe(imminent_df, use_container_width=True)
          else:
            st.success("👍 향후 7일 이내에 출고 임박한 긴급 건이 없습니다.")
        else:
          st.info("납기일 데이터를 확인할 수 없습니다.")

        st.markdown("---")

        # 2. 월별 출고 예정 현황 (최신/미래 시간 기준 초점)
        st.subheader("📅 월별 출고 예정 제품 리스트 및 건수")
        if delivery_col and not df["납기_dt"].isna().all():
          # 이미 지난 달은 제외하고 오늘 이후이거나 최근 유효한 월부터 표시
          df["출고월"] = df["납기_dt"].dt.strftime("%Y-%m")
          # 미출고 건 위주 또는 최신 순으로 월 정렬
          valid_months = (
              df[df["출고월"].notnull() & (df["출고월"] != "NaT")]
              .sort_values("출고월", ascending=True)["출고월"]
              .unique()
          )

          if len(valid_months) > 0:
            selected_month = st.selectbox(
                "출고 예정 월을 선택하세요", valid_months, index=0
            )
            month_df = df[df["출고월"] == selected_month]
            st.info(
                f"📌 [{selected_month}] 출고 예정 제품: 총"
                f" **{len(month_df)}건**"
            )
            st.dataframe(month_df, use_container_width=True)
        else:
          st.info("월별 출고 예정 데이터를 불러올 수 없습니다.")

        st.markdown("---")

        # 3. 통합 다중 조건 검색 (제품명, 폭 사이즈, 실사종)
        st.subheader("🔍 상세 조건 검색 (제품명 / 폭 / 실사종)")
        c1, c2, c3 = st.columns(3)
        with c1:
          q_name = st.text_input("🏷️ 제품명", "")
        with c2:
          q_width = st.text_input("📏 폭 사이즈 (예: 40)", "")
        with c3:
          q_item = st.text_input("🔖 실사종 / ITEM", "")

        search_df = df.copy()
        if q_name:
          search_df = search_df[
              search_df.astype(str)
              .apply(lambda row: row.str.contains(q_name, case=False))
              .any(axis=1)
          ]
        if q_width:
          w_col = [
              c for c in search_df.columns if "폭" in c or "width" in c.lower()
          ]
          if w_col:
            search_df = search_df[
                search_df[w_col[0]].astype(str).str.contains(q_width, case=False)
            ]
        if q_item:
          i_col = [
              c
              for c in search_df.columns
              if "ITEM" in c
              or "아이템" in c
              or "PILE" in c
              or "YARN" in c
          ]
          if i_col:
            search_df = search_df[
                search_df[i_col].astype(str).apply(
                    lambda row: row.str.contains(q_item, case=False)
                ).any(axis=1)
            ]

        st.write(f"검색 결과: 총 **{len(search_df)}건**")
        st.dataframe(search_df, use_container_width=True, height=500)

      # ====================================================
      # [메뉴 2] 이전 연도 아카이브 폴더
      # ====================================================
      elif menu_mode == "📁 이전 연도 아카이브":
        st.subheader("📁 이전 연도 수주/출고 아카이브 폴더")
        past_years = [y for y in years if y < latest_year]

        if past_years:
          tabs = st.tabs([str(py) + "년" for py in past_years])
          for idx, py in enumerate(past_years):
            with tabs[idx]:
              p_df = df[df["연도"] == py]
              st.write(f"**{py}년도 데이터** (총 {len(p_df)}건)")
              st.dataframe(p_df, use_container_width=True, height=600)
        else:
          st.info("조회할 이전 연도 데이터가 없습니다.")

      # ====================================================
      # [메뉴 3] SCM 통계 분석 그래프 폴더
      # ====================================================
      elif menu_mode == "📊 SCM 통계 분석 그래프":
        st.subheader("📊 SCM 통계 분석 리포트")

        g1, g2 = st.columns(2)
        with g1:
          st.markdown("#### 📅 월별 발주 건수 추이")
          if "발주서 수령_dt" in df.columns:
            df["발주월"] = df["발주서 수령_dt"].dt.strftime("%Y-%m")
            m_counts = df["발주월"].value_counts().sort_index().reset_index()
            m_counts.columns = ["월", "발주건수"]
            if not m_counts.empty:
              st.bar_chart(m_counts.set_index("월"))

        with g2:
          st.markdown("#### 🏢 대리점별 발주 비중 Top 10")
          ag_col = [c for c in df.columns if "대리점" in c or "AGENCY" in c]
          if ag_col:
            ag_counts = df[ag_col[0]].value_counts().head(10)
            if not ag_counts.empty:
              st.bar_chart(ag_counts)

        st.markdown("---")
        st.markdown("#### 📦 출고 완료 vs 미출고 현황 비율")
        if "출고 완료" in df.columns:
          status_counts = df["출고 완료"].fillna("진행중").value_counts()
          st.bar_chart(status_counts)

    else:
      st.warning("가져온 데이터가 비어있습니다. 시트 내용을 확인해 주세요.")

  except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
