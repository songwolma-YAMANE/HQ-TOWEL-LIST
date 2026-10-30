import base64
from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (와이드 모드)
st.set_page_config(
    page_title="본사 문직 제품 수주 및 출고 관리 시스템", layout="wide"
)


# 로컬 이미지 파일을 Base64로 변환하여 HTML에서 깨지지 않도록 처리하는 함수
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""


# 이미지 파일들을 Base64로 인코딩 (파이썬 파일과 같은 경로에 파일이 있어야 합니다)
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

            # 1. 통화 포맷 적용 ($) - 소수점 넷째 자리(:,.4f)까지 표시
            for col in df.columns:
                if (
                    "단가" in col
                    or "총액" in col
                    or "AMOUNT" in col
                    or "FOB" in col
                ):
                    df[col] = pd.to_numeric(
                        df[col]
                        .astype(str)
                        .str.replace("$", "", regex=False)
                        .str.replace(",", "", regex=False)
                        .str.strip(),
                        errors="coerce",
                    )
                    df[col] = df[col].apply(
                        lambda x: f"$ {x:,.4f}"
                        if pd.notnull(x) and x > 0
                        else ""
                    )

            # 날짜 데이터 정제 (변경하신 '납기 1차' 또는 기존 키워드 자동 인식)
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
            years = sorted(
                [int(y) for y in df["연도"].dropna().unique()], reverse=True
            )
            latest_year = years[0] if years else 2026

            # 발주서 수령일 기준 최신순(내림차순) 정렬
            df = df.sort_values(
                by="발주서 수령_dt", ascending=False
            ).reset_index(drop=True)

            # 불필요한 시스템 컬럼 제거 (4차, 5차 등 필요시 조정)
            cols_to_drop = [
                c
                for c in df.columns
                if c in ["발주서 수령_dt", "납기_dt", "연도", "출고월", "발주월"]
            ]
            display_df = df.drop(columns=cols_to_drop, errors="ignore")

            # 공통으로 쓰일 컬럼명 정의
            name_col = [
                c for c in df.columns if "제품명" in c or "KOREAN NAME" in c
            ]
            width_col = [
                c for c in df.columns if "폭" in c or "width" in c.lower()
            ]
            item_col = [
                c
                for c in df.columns
                if "ITEM" in c
                or "아이템" in c
                or "PILE" in c
                or "YARN" in c
            ]
            agency_col = [
                c for c in df.columns if "대리점" in c or "AGENCY" in c
            ]

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
                        latest_df_raw["출고 완료"].astype(str).str.upper()
                        == "O"
                    ]
                )
                uncompleted_count = total_ordered - completed_count

                col_k1, col_k2, col_k3 = st.columns(3)
                col_k1.metric(
                    label=f"🟢 {latest_year}년 오더 건수",
                    value=f"{total_ordered} 건",
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
                    not_completed_mask = (
                        df["출고 완료"].astype(str).str.upper() != "O"
                    )
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
                        st.success(
                            "👍 향후 7일 이내에 출고 임박한 긴급 건이 없습니다."
                        )
                else:
                    st.info("납기일 데이터를 확인할 수 없습니다.")

                # 3. 월별 출고 예정 현황 (미출고 기준)
                st.markdown("---")
                st.subheader(
                    "📅 월별 출고 예정 제품 리스트 및 건수 (미출고 기준)"
                )
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
                                "출고 예정 월을 선택하세요",
                                valid_months,
                                index=0,
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
                            "🎉 현재 모든 오더의 출고가 완료되어 미출고 건이"
                            " 없습니다!"
                        )
                else:
                    st.info("월별 출고 예정 데이터를 불러올 수 없습니다.")

                # 4. 메인 상세 조건 검색
                st.markdown("---")
                st.subheader(
                    "🔍 상세 조건 검색 (원하는 단어를 선택하거나 검색하세요)"
                )

                c1, c2, c3 = st.columns(3)
                with c1:
                    sel_name = st.selectbox(
                        "🏷️ 제품명 선택/검색",
                        ["전체 선택"] + all_names,
                        key="main_name",
                    )
                with c2:
                    sel_width = st.selectbox(
                        "📏 폭 사이즈 선택/검색",
                        ["전체 선택"] + all_widths,
                        key="main_width",
                    )
                with c3:
                    sel_item = st.selectbox(
                        "🔖 실사종 / ITEM 선택/검색",
                        ["전체 선택"] + all_items,
                        key="main_item",
                    )

                search_idx = df.index
                if sel_name and sel_name != "전체 선택":
                    match_mask = (
                        df[name_col[0]].astype(str).str.strip()
                        == str(sel_name).strip()
                    )
                    search_idx = search_idx.intersection(
                        df[match_mask].index
                    )
                if sel_width and sel_width != "전체 선택":
                    match_mask = (
                        df[width_col[0]].astype(str).str.strip()
                        == str(sel_width).strip()
                    )
                    search_idx = search_idx.intersection(
                        df[match_mask].index
                    )
                if sel_item and sel_item != "전체 선택":
                    match_mask = (
                        df[item_col[0]].astype(str).str.strip()
                        == str(sel_item).strip()
                    )
                    search_idx = search_idx.intersection(
                        df[match_mask].index
                    )

                search_df = display_df.loc[
                    display_df.index.intersection(search_idx)
                ]

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
                            p_df = display_df.loc[
                                display_df.index.intersection(p_idx)
                            ]
                            st.info(
                                f"📂 {py_val}년도 과거 오더 내역 (총"
                                f" {len(p_df)}건 출고 완료 데이터)"
                            )
                            st.dataframe(
                                p_df, use_container_width=True, height=400
                            )
                else:
                    st.info("조회 가능한 과거 연도 아카이브 데이터가 없습니다.")

            # ====================================================
            # [메뉴 2] SCM 통계 분석 그래프
            # ====================================================
            elif menu_choice == "📊 SCM 통계 분석 그래프":
                st.markdown("---")
                st.subheader("📊 연도별 및 상태별 SCM 통계 분석")

                yearly_counts = df["연도"].value_counts().reset_index()
                yearly_counts.columns = ["연도", "오더 건수"]
                yearly_counts = yearly_counts.sort_values("연도")

                col_stat1, col_stat2 = st.columns(2)

                with col_stat1:
                    st.markdown("### 📈 연도별 수주 건수 추이")
                    if not yearly_counts.empty:
                        st.bar_chart(
                            yearly_counts.set_index("연도"), color="#ff6b6b"
                        )
                    else:
                        st.info("표시할 연도별 데이터가 없습니다.")

                with col_stat2:
                    st.markdown("### 🏷️ 주요 대리점별 오더 비중")
                    if agency_col:
                        agency_counts = (
                            df[agency_col[0]].value_counts().reset_index()
                        )
                        agency_counts.columns = ["대리점명", "건수"]
                        st.dataframe(
                            agency_counts, use_container_width=True, height=250
                        )
                    else:
                        st.info("대리점 컬럼을 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"데이터를 불러오거나 처리하는 중 오류가 발생했습니다: {e}")
