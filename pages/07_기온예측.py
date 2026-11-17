import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import os

# Linux(Streamlit Cloud) 환경에서 한글 폰트 설정 (나눔고딕 자동 적용)
if os.name != 'nt':
    plt.rc('font', family='NanumGothic')
else:
    plt.rc('font', family='Malgun Gothic')

mpl.rcParams['axes.unicode_minus'] = False  # 마이너스 부호 깨짐 방지

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

# 페이지 기본 설정
st.set_page_config(page_title="기온 예측 및 머신러닝 알고리즘 비교", page_icon="🌡️", layout="wide")

st.title("🌡️ 3가지 머신러닝 알고리즘을 이용한 월별 평균기온 예측")
st.markdown("사용자가 선택한 월의 과거 데이터를 바탕으로 **선형회귀, 랜덤 포레스트, SVR** 알고리즘이 각각 어떻게 작동하고 예측하는지 시각화합니다.")

# 1. 데이터 로드 및 전처리
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path, encoding="cp949", skiprows=11)
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="utf-8", skiprows=11)
    
    df.columns = df.columns.str.strip()
    df["일시"] = df["일시"].astype(str).str.strip()
    df["연도"] = df["일시"].str.split("-").str[0].astype(int)
    df["월"] = df["일시"].str.split("-").str[1].astype(int)
    df = df.dropna(subset=["평균기온(℃)"]).copy()
    return df

try:
    df = load_data("temperature.csv")
except FileNotFoundError:
    st.error("⚠️ `temperature.csv` 파일을 찾을 수 없습니다. 같은 폴더에 파일을 위치시켜 주세요.")
    st.stop()

# 2. 사이드바 설정
st.sidebar.header("⚙️ 분석 설정")
selected_month = st.sidebar.selectbox("분석할 월(Month) 선택", list(range(1, 13)), index=7)
max_data_year = int(df["연도"].max())
target_year = st.sidebar.number_input("예측할 연도 입력", min_value=max_data_year + 1, max_value=2150, value=2030, step=1)

algo_choice = st.sidebar.selectbox(
    "사용할 알고리즘 선택",
    ["전체 비교 (3개 동시 비교)", "1. 선형회귀 (Linear Regression)", "2. 랜덤 포레스트 (Random Forest)", "3. 서포트 벡터 머신 (SVR)"]
)

# 데이터 필터링
month_df = df[df["월"] == selected_month].sort_values("연도")
X = month_df[["연도"]].values
y = month_df["평균기온(℃)"].values

# 3. 모델 학습 및 예측 준비
models = {
    "선형회귀": LinearRegression(),
    "랜덤 포레스트": RandomForestRegressor(n_estimators=100, random_state=42),
    "SVR": make_pipeline(StandardScaler(), SVR(kernel='rbf', C=10, gamma=0.1))
}

years_smooth = np.linspace(X.min(), max(target_year, X.max()), 300).reshape(-1, 1)

predictions = {}
model_trends = {}

for name, model in models.items():
    model.fit(X, y)
    predictions[name] = model.predict(np.array([[target_year]]))[0]
    model_trends[name] = model.predict(years_smooth)

# 4. KPI 지표 출력
st.subheader(f"📊 {target_year}년 {selected_month}월 기온 예측 결과 비교")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="선형회귀 예측 기온", value=f"{predictions['선형회귀']:.2f} ℃")
with col2:
    st.metric(label="랜덤 포레스트 예측 기온", value=f"{predictions['랜덤 포레스트']:.2f} ℃")
with col3:
    st.metric(label="SVR 예측 기온", value=f"{predictions['SVR']:.2f} ℃")

# 5. 시각화 그래프
fig, ax = plt.subplots(figsize=(12, 6))

ax.scatter(X, y, color="black", alpha=0.5, s=40, label="실제 관측 기온")

colors = {"선형회귀": "#d62728", "랜덤 포레스트": "#2ca02c", "SVR": "#1f77b4"}
styles = {"선형회귀": "-", "랜덤 포레스트": "--", "SVR": "-."}

if algo_choice == "전체 비교 (3개 동시 비교)":
    for name in models:
        ax.plot(years_smooth, model_trends[name], color=colors[name], linestyle=styles[name], linewidth=2, label=f"{name} 모델 추세")
        ax.scatter([target_year], [predictions[name]], color=colors[name], s=120, zorder=5, marker="*")
else:
    selected_name = algo_choice.split(". ")[1]
    if selected_name == "선형회귀":
        y_pred_past = models["선형회귀"].predict(X)
        for i in range(len(X)):
            ax.plot([X[i][0], X[i][0]], [y[i], y_pred_past[i]], color="gray", linestyle=":", alpha=0.5)
    
    ax.plot(years_smooth, model_trends[selected_name], color=colors[selected_name], linestyle="-", linewidth=2.5, label=f"{selected_name} 추세선")
    ax.scatter([target_year], [predictions[selected_name]], color=colors[selected_name], s=200, zorder=5, marker="*", label=f"{target_year}년 예측: {predictions[selected_name]:.2f}℃")

ax.set_title(f"서울 {selected_month}월 기온 예측 모델 비교 ({int(X.min())}~{target_year})", fontsize=14, fontweight="bold")
ax.set_xlabel("연도", fontsize=11)
ax.set_ylabel("평균기온 (℃)", fontsize=11)
ax.grid(True, linestyle="--", alpha=0.4)
ax.legend(loc="upper left", fontsize=10)

st.pyplot(fig)

# 6. 알고리즘 쉬운 설명
st.markdown("---")
st.subheader("💡 사용된 3가지 머신러닝 알고리즘의 작동 원리")

tab1, tab2, tab3 = st.tabs(["1. 선형회귀 (Linear Regression)", "2. 랜덤 포레스트 (Random Forest)", "3. 서포트 벡터 머신 (SVR)"])

with tab1:
    st.markdown("""
    * **어떻게 작동하나요?** 데이터 점들 사이를 관통하는 **하나의 반듯한 직선**을 긋습니다.
    * **시각적 특징:** 그래프에서 일정한 기울기를 가진 **빨간 직선**으로 나타납니다. 장기적인 기온 상승/하강 트렌드를 단순하고 명확하게 파악할 때 유용합니다.
    """)

with tab2:
    st.markdown("""
    * **어떻게 작동하나요?** 수많은 **의사결정나무(Decision Tree)**를 숲처럼 여러 개 모아서, 각 나무들이 내린 예측 결과의 **평균값**을 최종 예측값으로 사용합니다.
    * **시각적 특징:** 계단식 또는 구간별로 꺾이는 형태로 나타나며, 과거 데이터의 급격한 변동이나 특이점을 유연하게 반영합니다.
    """)

with tab3:
    st.markdown("""
    * **어떻게 작동하나요?** 데이터들 사이에 **허용 가능한 오차 범위(마진 폭)**를 설정하고, 그 경계선 안에 데이터가 최대한 많이 들어가도록 부드러운 곡선 형태의 최적의 함수를 찾아냅니다.
    * **시각적 특징:** 부드럽고 유연한 곡선 형태로 미래 추세를 나타내며, 이상치(Outlier)의 영향을 적게 받아 안정적입니다.
    """)
