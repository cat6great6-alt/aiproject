import os
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import KBinsDiscretizer

# 페이지 설정
st.set_page_config(
    page_title="연도별 출생률 예측",
    page_icon="👶",
    layout="wide"
)

# 1. 데이터 로드 및 전처리 함수 (루트 경로 및 현재 경로 모두 탐색)
@st.cache_data
def load_data(file_name):
    possible_paths = [
        file_name,
        os.path.join("..", file_name),
        os.path.join(os.path.dirname(__file__), file_name),
        os.path.join(os.path.dirname(__file__), "..", file_name)
    ]
    
    target_path = None
    for path in possible_paths:
        if os.path.exists(path):
            target_path = path
            break
            
    if target_path is None:
        return None

    # CP949 / EUC-KR / UTF-8 인코딩 자동 대응
    df = None
    for enc in ['cp949', 'euc-kr', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(target_path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        return None

    # 행정구역명 정리 (괄호 및 행정코드 제거)
    df['지역명'] = df['행정구역'].str.replace(r'\s*\(\d+\)', '', regex=True).str.strip()

    years = list(range(2016, 2026))
    records = []

    for _, row in df.iterrows():
        region = row['지역명']
        base_val = int(str(row['2016년_계']).replace(',', ''))
        prev_val = None

        for y in years:
            col_name = f"{y}년_계"
            val = int(str(row[col_name]).replace(',', ''))
            
            # 2016년 대비 출생률 지수 (%)
            index_rate = round((val / base_val) * 100, 2)
            # 전년 대비 출생 증감률 (%)
            yoy_rate = round(((val - prev_val) / prev_val) * 100, 2) if prev_val is not None else 0.0

            records.append({
                '지역명': region,
                '연도': y,
                '출생등록수(명)': val,
                '기준대비_출생률(%)': index_rate,
                '전년대비_증감률(%)': yoy_rate
            })
            prev_val = val

    return pd.DataFrame(records)

CSV_FILE = "2016_2025_주민등록인구기타현황(출생등록)_연간.csv"
data = load_data(CSV_FILE)

if data is None:
    st.error(f"'{CSV_FILE}' 파일을 찾을 수 없습니다. GitHub 저장소 최상위 폴더에 CSV 파일을 업로드해주세요.")
    st.stop()

# 화면 상단 제목
st.title("📊 연도별 출생률 예측 (분류 알고리즘 기반)")
st.markdown(
    "분류 알고리즘인 **랜덤 포레스트 분류기(RandomForestClassifier)**를 사용하여 "
    "선택한 지역의 연도별 출생률 구간 및 예측값을 산출합니다."
)

# 2. 사용자 입력 영역 및 입력 가능 범위 사전 안내
st.sidebar.header("⚙️ 예측 조건 입력")

regions = data['지역명'].unique().tolist()
selected_region = st.sidebar.selectbox("1. 행정구역 선택", regions, index=0)

metric_option = st.sidebar.radio(
    "2. 출생률 지표 선택",
    ["기준대비_출생률(%)", "전년대비_증감률(%)"],
    help="기준대비_출생률(%): 2016년 출생아 수를 100%로 본 비율 / 전년대비_증감률(%): 직전 연도 대비 변화율"
)

MIN_YEAR = 2016
MAX_YEAR = 2035

# 사용자가 입력할 수 있는 값의 범위 미리 안내
st.sidebar.info(
    f"📌 **입력 가능한 연도 범위 안내**\n\n"
    f"- **입력 가능 범위:** `{MIN_YEAR}년` ~ `{MAX_YEAR}년`\n"
    f"- `2016 ~ 2025년`: 실제 통계 데이터 구간\n"
    f"- `2026 ~ 2035년`: 머신러닝 미래 예측 구간"
)

target_year = st.sidebar.number_input(
    f"3. 예측할 연도 입력 ({MIN_YEAR} ~ {MAX_YEAR})",
    min_value=MIN_YEAR,
    max_value=MAX_YEAR,
    value=2026,
    step=1
)

# 선택된 지역 데이터 추출
region_df = data[data['지역명'] == selected_region].copy().reset_index(drop=True)

# 3. 분류 알고리즘(RandomForestClassifier) 학습 및 예측
n_bins = 5
X = region_df[['
