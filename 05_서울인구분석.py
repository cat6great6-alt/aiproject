import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 페이지 기본 설정
st.set_page_config(
    page_title="서울시 연령별 인구 분석 시각화",
    page_icon="📊",
    layout="wide"
)

# CSV 데이터 로드 (pages 폴더 기준 상위 폴더의 population.csv 경로 설정)
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, '..', 'population.csv')
    df = pd.read_csv(file_path, encoding='cp949')
    return df

df = load_data()

st.title("📊 행정구역/연도/성별 연령별 인구 분석")
st.markdown("선택한 조건에 따른 연령구간별 인구수를 꺾은선 그래프(무지개색 적용)로 확인할 수 있습니다.")

# ---------------- 사용자 입력 사이드바 ----------------
st.sidebar.header("🔍 조회 조건 선택")

# 1. 행정구역 목록 추출
district_list = df['행정구역'].tolist()
selected_district = st.sidebar.selectbox("행정구역 선택", district_list, index=0)

# 2. 연도 목록 추출 (2020 ~ 2025)
years = sorted(list(set([col[:4] for col in df.columns if col[:4].isdigit()])))
selected_year = st.sidebar.selectbox("연도 선택", years, index=len(years)-1)

# 3. 성별 선택
gender_map = {
    "전체": "",
    "남성": "남_",
    "여성": "여_"
}
selected_gender = st.sidebar.radio("성별 선택", list(gender_map.keys()), index=0)

# ---------------- 데이터 처리 ----------------
age_groups = [
    '0~9세', '10~19세', '20~29세', '30~39세', '40~49세', 
    '50~59세', '60~69세', '70~79세', '80~89세', '90~99세', '100세 이상'
]

gender_prefix = gender_map[selected_gender]
target_row = df[df['행정구역'] == selected_district].iloc[0]

population_values = []
for age in age_groups:
    col_name = f"{selected_year}년_{gender_prefix}거주자_{age}"
    val_str = str(target_row[col_name]).replace(',', '')
    population_values.append(int(val_str))

# ---------------- 그래프 생성 (Plotly) ----------------
# N개 선 구간에 적용할 무지개 색상 (Red -> Violet)
rainbow_colors = [
    '#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#00FFFF', 
    '#0000FF', '#4B0082', '#9400D3', '#FF007F', '#FF1493'
]

fig = go.Figure()

# 꺾은선 각 선분에 무지개 스펙트럼 색상 부여
for i in range(len(age_groups) - 1):
    fig.add_trace(go.Scatter(
        x=[age_groups[i], age_groups[i+1]],
        y=[population_values[i], population_values[i+1]],
        mode='lines+markers',
        line=dict(color=rainbow_colors[i % len(rainbow_colors)], width=4),
        marker=dict(size=8, color=rainbow_colors[i % len(rainbow_colors)]),
        hoverinfo='x+y',
        showlegend=False
    ))

# Y축 범위 및 1,000명 단위 구분선(dtick=1000) 설정
max_val = max(population_values)
y_max = int(np.ceil(max_val / 1000.0) * 1000) + 1000 if max_val > 0 else 10000

fig.update_layout(
    title=f"<b>[{selected_district}] {selected_year}년 ({selected_gender}) 연령별 인구수</b>",
    xaxis_title="<b>나이 (연령구간)</b>",
    yaxis_title="<b>인구수 (명)</b>",
    height=600,
    hovermode="x unified",
    template="plotly_white",
    yaxis=dict(
        tickmode='linear',
        tick0=0,
        dtick=1000,  # 1000명 단위로 눈금표시 및 격자선(grid) 형성
        showgrid=True,
        gridcolor='rgba(200, 200, 200, 0.4)',
        range=[0, y_max]
    ),
    xaxis=dict(
        showgrid=True,
        gridcolor='rgba(230, 230, 230, 0.5)'
    )
)

# 화면에 그래프 출력
st.plotly_chart(fig, use_container_width=True)

# ---------------- 주요 데이터 요약 ----------------
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("최대 인구 연령대", f"{age_groups[np.argmax(population_values)]}", f"{max(population_values):,} 명")
with col2:
    st.metric("최소 인구 연령대", f"{age_groups[np.argmin(population_values)]}", f"{min(population_values):,} 명")
with col3:
    st.metric("총 인구수 합계", f"{sum(population_values):,} 명")
