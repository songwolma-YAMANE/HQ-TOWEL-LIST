import base64
from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (와이드 모드)
st.set_page_config(
    page_title="본사 문직 제품 수주 및 출고 관리 시스템", layout="wide"
)


# 로컬 이미지 파일을 Base64로 변환하는 함수
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""


# 이미지 파일을 Base64로 인코딩 (파일명이 다를 경우 파일명을 확인해주세요)
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

# (이하 기존 코드 동일하게 유지...)
