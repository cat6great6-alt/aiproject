import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib  # Streamlit Cloud(Linux) 한글 깨짐 방지
from sklearn.linear_model import LinearRegression

# 페이지 기본 설정
st.set_page_config(page_title="기온 예측 및 선형회귀 시각화", page_icon="🌡️", layout="wide")

st.title("🌡️ 월별 평균기온 추이 및 선형회귀(Linear Regression) 예측")
st.markdown("과거 기상 데이터를 바탕으로 **선형회귀 알고리즘**이 어떻게 미래 기온을 예측하는지 시각적으로 확인해보세요.")

# 1. 데이터 로드 및 전처리 (캐싱을 통해 속도 최적화)
@st.cache_data
def load_data(file_path):
    # 기상청 CSV 파일 구조 반영 (상단 11줄 메타데이터 제외, cp949/utf-8 자동 대응)
    try:
        df = pd.read_csv(file_path, encoding="cp949", skiprows=11)
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="utf-8", skiprows=11)
    
    # 컬럼명 및 문자열 앞뒤 공백/탭 제거
    df.columns = df.columns.str.strip()
    df["일시"] = df["일시"].astype(str).str.strip()
    
    # 연도와 월 분리
    df["연도"] = df["일시"].str.split("-").str[0].astype(int)
    df["월"] = df["일시"].str.split("-").str[1].astype(int)
    
    # 평균기온 결측치(NaN) 제거
    df = df.dropna(subset=["평균기온(℃)"]).copy()
    return df

try:
    df = load_data("temperature.csv")
except FileNotFoundError:
    st.error("⚠️ `temperature.csv` 파일을 찾을 수 없습니다. 같은 폴더에 파일을 위치시켜 주세요.")
    st.stop()

# 2. 사이드바: 사용자 입력 (월, 예측 연도)
st.sidebar.header("⚙️ 예측 조건 설정")
selected_month = st.sidebar.selectbox("분석할 월(Month)을 선택하세요", list(range(1, 13)), index=7) # 기본값 8월
max_data_year = int(df["연도"].max())
target_year = st.sidebar.number_input(
    "예측할 연도(Year)를 입력하세요",
    min_value=max_data_year + 1,
    max_value=2150,
    value=2030,
    step=1
)

# 선택한 월 데이터 필터링
month_df = df[df["월"] == selected_month].sort_values("연도")

# 3. 선형회귀 모델 학습 및 예측
X = month_df[["연도"]].values  # 독립변수 (연도)
y = month_df["평균기온(℃)"].values  # 종속변수 (평균기온)

model = LinearRegression()
model.fit(X, y)

# 학습 데이터 구간 추세선 및 미래 예측값 계산
y_pred_past = model.predict(X)
predicted_temp = model.predict(np.array([[target_year]]))[0]

# 기울기(1년당 기온 변화량) 및 절편
slope = model.coef_[0]
intercept = model.intercept_

# 4. 상단 핵심 지표(KPI) 표시
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label=f"{target_year}년 {selected_month}월 예측 평균기온",
        value=f"{predicted_temp:.2f} ℃",
        delta=f"과거 전체 평균 대비 {predicted_temp - y.mean():+.2f} ℃"
    )
with col2:
    st.metric(
        label=f"역대 {selected_month}월 평균기온 ({int(month_df['연도'].min())}~{max_data_year})",
        value=f"{y.mean():.2f} ℃"
    )
with col3:
    st.metric(
        label="연평균 기온 상승 추세 (기울기)",
        value=f"{slope:+.4f} ℃/년",
        delta=f"10년당 {slope*10:+.2f} ℃ 변화"
    )

# 5. 선형회귀 작동 원리 시각화 그래프
st.subheader(f"📈 {selected_month}월 역대 평균기온 및 {target_year}년 선형회귀 예측 그래프")

fig, ax = plt.subplots(figsize=(12, 6))

# (1) 실제 관측 데이터 산점도 (파란 점)
ax.scatter(
    month_df["연도"], y,
    color="#1f77b4", alpha=0.65, s=45,
    label=f"실제 관측 기온 ({int(month_df['연도'].min())}~{max_data_year}년)"
)

# (2) 오차(잔차) 시각화: 실제 데이터 점과 회귀선 사이의 수직 거리 (회색 점선)
for i in range(len(X)):
    ax.plot(
        [X[i][0], X[i][0]], [y[i], y_pred_past[i]],
        color="gray", linestyle=":", linewidth=0.8, alpha=0.5
    )
# 범례용 더미 라인 (잔차 설명)
ax.plot([], [], color="gray", linestyle=":", linewidth=1.2, label="오차(잔차): 실제값과 추세선의 차이")

# (3) 과거 데이터 학습 추세선 (빨간 실선)
ax.plot(
    month_df["연도"], y_pred_past,
    color="#d62728", linewidth=2.5,
    label=f"선형회귀 추세선 (기울기: {slope:+.4f}℃/년)"
)

# (4) 미래 예측 구간 연장선 (주황 점선)
future_years = np.array([[max_data_year], [target_year]])
future_preds = model.predict(future_years)
ax.plot(
    future_years.flatten(), future_preds,
    color="#ff7f0e", linestyle="--", linewidth=2.5,
    label="미래 예측 연장선"
)

# (5) 최종 예측 지점 강조 (초록 별)
ax.scatter(
    [target_year], [predicted_temp],
    color="#2ca02c", s=220, zorder=5, edgecolors="black", marker="*",
    label=f"{target_year}년 예측 기온: {predicted_temp:.2f}℃"
)

# 예측 지점 텍스트 주석 표시
ax.annotate(
    f"{target_year}년 예측\n{predicted_temp:.2f}℃",
    xy=(target_year, predicted_temp),
    xytext=(target_year - (target_year - month_df["연도"].min()) * 0.12, predicted_temp + (y.max() - y.min()) * 0.12),
    arrowprops=dict(facecolor="#2ca02c", shrink=0.08, width=1.5, headwidth=7),
    fontsize=11, fontweight="bold", color="#1b6b1b",
    bbox=dict(boxstyle="round,pad=0.4", fc="#eaffea", ec="#2ca02c", lw=1.2)
)

ax.set_title(f"서울 {selected_month}월 평균기온 변화 및 선형회귀 예측 모델", fontsize=15, fontweight="bold", pad=15)
ax.set_xlabel("연도 (Year)", fontsize=12)
ax.set_ylabel("평균기온 (℃)", fontsize=12)
ax.grid(True, linestyle="--", alpha=0.35)
ax.legend(loc="upper left", fontsize=10, frameon=True, shadow=True)

st.pyplot(fig)

# 6. 그래프 하단: 선형회귀 알고리즘 쉬운 설명
st.markdown("---")
st.subheader("💡 그래프 속 '선형회귀(Linear Regression)' 알고리즘은 어떻게 작동할까요?")

st.info(f"""
**한 줄 요약:** 과거 데이터 점들 사이를 가장 잘 가로지르는 **'최적의 직선(추세선)'**을 하나 긋고, 그 직선을 미래 연도까지 쭉 연장해서 기온을 예측하는 방법입니다!

1. **파란 점 (과거 데이터):** {int(month_df['연도'].min())}년부터 {max_data_year}년까지 매년 {selected_month}월의 실제 평균기온을 찍은 점입니다.
2. **회색 점선 (오차 찾기):** 어떤 직선을 그어야 데이터를 가장 잘 설명할 수 있을까요? 선형회귀 알고리즘은 파란 점들과 직선 사이의 수직 거리(**오차**)들의 제곱 합이 **가장 작아지는(최소제곱법)** 완벽한 각도의 직선을 찾아냅니다.
3. **빨간 실선 (학습된 규칙):** 그렇게 찾은 최적의 직선입니다. 현재 데이터에 따르면 {selected_month}월 기온은 1년마다 평균 **`{slope:+.4f}℃`**씩 변하는 규칙(기울기)을 보입니다.
   * *적용된 예측 공식:* `예측 기온 = ({slope:.4f} × 연도) + ({intercept:.2f})`
4. **주황 점선 & 초록 별 (미래 예측):** 찾아낸 빨간 직선의 기울기 그대로 **{target_year}년** 위치까지 선을 연장(주황 점선)하여 만나는 지점(초록 별)을 읽으면 **`{predicted_temp:.2f}℃`**라는 예측값이 나옵니다.
""")

# 7. 원본 데이터 확인 토글
with st.expander(f"📊 {selected_month}월 과거 기온 데이터 표로 보기"):
    display_df = month_df[["지점명", "일시", "평균기온(℃)", "평균최고기온(℃)", "평균최저기온(℃)"]].sort_values("일시", ascending=False)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
