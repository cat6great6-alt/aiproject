
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import KBinsDiscretizer

# 페이지 기본 설정
st.set_page_config(
    page_title="연도별 출생률 예측 (분류 모델 기반)",
    page_icon="👶",
    layout="wide"
)

# 1. 데이터 로드 및 전처리 함수
@st.cache_data
def load_data(file_path):
    # CP949 / EUC-KR 인코딩 대응
    for enc in ['cp949', 'euc-kr', 'utf-8-sig']:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue

    # 행정구역명 정리 (괄호 및 코드 제거)
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
                '출생등록수': val,
                '기준대비_출생률(%)': index_rate,
                '전년대비_증감률(%)': yoy_rate
            })
            prev_val = val

    return pd.DataFrame(records)

# 데이터 불러오기
CSV_FILE = "2016_2025_주민등록인구기타현황(출생등록)_연간.csv"
try:
    data = load_data(CSV_FILE)
except FileNotFoundError:
    st.error(f"'{CSV_FILE}' 파일을 찾을 수 없습니다. 같은 디렉토리에 CSV 파일을 업로드해주세요.")
    st.stop()

# 타이틀 및 설명
st.title("📊 서울특별시 및 자치구 연도별 출생률 예측 대시보드")
st.markdown(
    "2016~2025년 주민등록 출생등록 데이터를 학습한 **랜덤 포레스트 분류기(RandomForestClassifier)**를 통해 "
    "특정 연도의 출생률 구간 및 예측치를 산출합니다."
)

# 사이드바: 조건 설정 및 입력 범위 안내
st.sidebar.header("⚙️ 예측 조건 설정")

regions = data['지역명'].unique().tolist()
selected_region = st.sidebar.selectbox("1. 분석할 행정구역 선택", regions, index=0)

metric_option = st.sidebar.radio(
    "2. 출생률 지표 기준 선택",
    ["기준대비_출생률(%)", "전년대비_증감률(%)"],
    help="기준대비 출생률은 2016년 출생아 수를 100%로 본 상대 비율이며, 전년대비 증감률은 직전 연도 대비 변화율입니다."
)

# 입력 가능한 연도 범위 안내
MIN_YEAR = 2016
MAX_YEAR = 2035
st.sidebar.info(
    f"📌 **입력 가능한 연도 범위 안내**\n\n"
    f"- **최소 연도:** {MIN_YEAR}년 (학습 데이터 시작 연도)\n"
    f"- **최대 연도:** {MAX_YEAR}년 (단기 시계열 외삽 허용 한계)\n"
    f"- *2016~2025년은 실제 관측 데이터가 존재하며, 2026~2035년은 미래 예측 구간입니다.*"
)

target_year = st.sidebar.number_input(
    "3. 예측할 연도 입력 (2016 ~ 2035)",
    min_value=MIN_YEAR,
    max_value=MAX_YEAR,
    value=2026,
    step=1
)

# 선택된 지역 데이터 필터링
region_df = data[data['지역명'] == selected_region].copy().reset_index(drop=True)

# 2. 분류 알고리즘(RandomForestClassifier) 학습 및 예측
# 연속형 출생률 데이터를 5개의 구간(Class)으로 이산화하여 분류 모델 학습
n_bins = 5
X = region_df[['연도']].values
y_continuous = region_df[metric_option].values

# 구간화 (KBinsDiscretizer)
discretizer = KBinsDiscretizer(n_bins=n_bins, encode='ordinal', strategy='quantile')
y_class = discretizer.fit_transform(y_continuous.reshape(-1, 1)).ravel().astype(int)

# 분류 모델 선정: RandomForestClassifier
clf = RandomForestClassifier(n_estimators=200, max_depth=4, random_state=42)
clf.fit(X, y_class)

# 사용자 입력 연도에 대한 클래스 예측 및 확률 기반 기댓값 산출
pred_class = clf.predict([[target_year]])[0]
pred_proba = clf.predict_proba([[target_year]])[0]

# 각 클래스별 평균 출생률 계산 (클래스 -> 대표 수치 매핑)
class_means = {}
for c in range(n_bins):
    vals = y_continuous[y_class == c]
    class_means[c] = np.mean(vals) if len(vals) > 0 else np.mean(y_continuous)

# 분류 확률 가중 평균을 통한 최종 예측 출생률 산출
classes_learned = clf.classes_
predicted_rate = sum(prob * class_means[c] for c, prob in zip(classes_learned, pred_proba))
predicted_rate = round(predicted_rate, 2)

# 구간 라벨 생성
bin_edges = discretizer.bin_edges_[0]
class_labels = [
    f"구간 {i+1} ({bin_edges[i]:.1f}% ~ {bin_edges[i+1]:.1f}%)"
    for i in range(n_bins)
]

# 3. 예측 결과 요약 카드 표시
st.subheader(f"🔍 [{selected_region}] {target_year}년 예측 결과")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label=f"{target_year}년 예측 {metric_option}",
        value=f"{predicted_rate}%"
    )
with col2:
    st.metric(
        label="분류 알고리즘 예측 구간 (Class)",
        value=f"구간 {pred_class + 1} / {n_bins}"
    )
with col3:
    actual_row = region_df[region_df['연도'] == target_year]
    if not actual_row.empty:
        actual_val = actual_row[metric_option].values[0]
        st.metric(label="실제 관측치 (2016~2025)", value=f"{actual_val}%")
    else:
        st.metric(label="데이터 구분", value="미래 예측치 (미관측)")

st.caption(
    f"※ 선정된 분류 모델: **RandomForestClassifier** | "
    f"예측된 구간 범위: **{class_labels[pred_class]}** (해당 구간 확률: {max(pred_proba)*100:.1f}%)"
)

# 4. 시각화 (가로축: 연도, 세로축: 출생률, 사용자 입력값 빨간색 표시)
st.subheader(f"📈 연도별 출생률 추이 및 {target_year}년 예측 위치")

fig = go.Figure()

# 기존 관측 데이터 (2016~2025) 라인 및 마커
fig.add_trace(go.Scatter(
    x=region_df['연도'],
    y=region_df[metric_option],
    mode='lines+markers',
    name='실제 데이터 (2016~2025)',
    line=dict(color='#1f77b4', width=3),
    marker=dict(size=8, color='#1f77b4')
))

# 미래 연도(2026~입력 연도)인 경우 추세 연결선 추가
if target_year > 2025:
    future_years = list(range(2025, target_year + 1))
    future_preds = []
    for fy in future_years:
        if fy == 2025:
            future_preds.append(region_df[region_df['연도'] == 2025][metric_option].values[0])
        else:
            p_prob = clf.predict_proba([[fy]])[0]
            p_val = sum(prob * class_means[c] for c, prob in zip(classes_learned, p_prob))
            future_preds.append(round(p_val, 2))

    fig.add_trace(go.Scatter(
        x=future_years,
        y=future_preds,
        mode='lines',
        name='예측 연결선',
        line=dict(color='gray', width=2, dash='dash')
    ))

# 사용자가 입력한 연도 지점 빨간색으로 강조 표시
fig.add_trace(go.Scatter(
    x=[target_year],
    y=[predicted_rate],
    mode='markers+text',
    name=f'사용자 입력 ({target_year}년 예측)',
    marker=dict(size=16, color='red', symbol='circle', line=dict(width=2, color='darkred')),
    text=[f"  {target_year}년: {predicted_rate}%"],
    textposition="top center",
    textfont=dict(color="red", size=14, family="Arial Black")
))

# 수직 보조선 추가
fig.add_vline(
    x=target_year,
    line_width=1.5,
    line_dash="dot",
    line_color="red"
)

fig.update_layout(
    xaxis_title="연도 (Year)",
    yaxis_title=metric_option,
    xaxis=dict(
        tickmode='linear',
        dtick=1,
        range=[MIN_YEAR - 0.5, max(2026, target_year) + 0.5]
    ),
    hovermode="x unified",
    template="plotly_white",
    height=500,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# 하단 원본 및 가공 데이터 테이블 확인
with st.expander("📋 선택 지역의 연도별 데이터 상세 보기"):
    st.dataframe(region_df, use_container_width=True)
