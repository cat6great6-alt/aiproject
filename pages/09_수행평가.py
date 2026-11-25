import os
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import KBinsDiscretizer

st.set_page_config(
    page_title="연도별 출생률 예측",
    page_icon="👶",
    layout="wide"
)


@st.cache_data
def load_data(file_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        file_name,
        os.path.join("..", file_name),
        os.path.join(base_dir, file_name),
        os.path.join(base_dir, "..", file_name),
    ]

    found_path = None
    for path in candidates:
        if os.path.exists(path):
            found_path = path
            break

    if found_path is None:
        return None

    df = None
    for enc in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            df = pd.read_csv(found_path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        return None

    df["지역명"] = df["행정구역"].astype(str).str.replace(r"\s*\(\d+\)", "", regex=True).str.strip()

    years = list(range(2016, 2026))
    rows = []

    for _, row in df.iterrows():
        region = row["지역명"]
        base_val = int(str(row["2016년_계"]).replace(",", "").strip())
        prev_val = None

        for y in years:
            col_name = str(y) + "년_계"
            val = int(str(row[col_name]).replace(",", "").strip())

            index_rate = round((val / base_val) * 100, 2)
            if prev_val is not None and prev_val != 0:
                yoy_rate = round(((val - prev_val) / prev_val) * 100, 2)
            else:
                yoy_rate = 0.0

            rows.append({
                "지역명": region,
                "연도": y,
                "출생등록수(명)": val,
                "기준대비_출생률(%)": index_rate,
                "전년대비_증감률(%)": yoy_rate,
            })
            prev_val = val

    return pd.DataFrame(rows)


CSV_NAME = "2016_2025_주민등록인구기타현황(출생등록)_연간.csv"
data = load_data(CSV_NAME)

if data is None:
    st.error("CSV 파일을 찾을 수 없습니다. GitHub 저장소 최상위 폴더에 CSV 파일이 있는지 확인해주세요.")
    st.stop()

st.title("연도별 출생률 예측 (분류 알고리즘 기반)")
st.write("RandomForestClassifier 분류 알고리즘을 사용해 선택한 지역의 연도별 출생률 구간과 예측값을 보여줍니다.")

MIN_YEAR = 2016
MAX_YEAR = 2035

st.sidebar.header("예측 조건 설정")
regions = data["지역명"].unique().tolist()
selected_region = st.sidebar.selectbox("행정구역 선택", regions)

metric_option = st.sidebar.radio(
    "출생률 지표 선택",
    ["기준대비_출생률(%)", "전년대비_증감률(%)"],
)

st.sidebar.info(
    "입력 가능 연도 범위: 2016년 ~ 2035년\n"
    "- 2016~2025년: 실제 관측 데이터 구간\n"
    "- 2026~2035년: 예측 구간"
)

target_year = st.sidebar.number_input(
    "예측할 연도 입력 (2016 ~ 2035)",
    min_value=MIN_YEAR,
    max_value=MAX_YEAR,
    value=2026,
    step=1,
)

region_df = data[data["지역명"] == selected_region].copy().reset_index(drop=True)

n_bins = 5
X = region_df[["연도"]].values
y_cont = region_df[metric_option].values

discretizer = KBinsDiscretizer(n_bins=n_bins, encode="ordinal", strategy="quantile")
y_cls = discretizer.fit_transform(y_cont.reshape(-1, 1)).ravel().astype(int)

clf = RandomForestClassifier(n_estimators=200, max_depth=4, random_state=42)
clf.fit(X, y_cls)

pred_class = int(clf.predict([[target_year]])[0])
pred_proba = clf.predict_proba([[target_year]])[0]

class_means = {}
for c in range(n_bins):
    vals = y_cont[y_cls == c]
    if len(vals) > 0:
        class_means[c] = float(np.mean(vals))
    else:
        class_means[c] = float(np.mean(y_cont))

predicted_rate = 0.0
for cls_idx, prob in zip(clf.classes_, pred_proba):
    predicted_rate += float(prob) * class_means[int(cls_idx)]
predicted_rate = round(predicted_rate, 2)

edges = discretizer.bin_edges_[0]
low_edge = round(float(edges[pred_class]), 1)
high_edge = round(float(edges[pred_class + 1]), 1)

st.subheader("예측 결과")
c1, c2, c3 = st.columns(3)
c1.metric(label=str(target_year) + "년 예측 " + metric_option, value=str(predicted_rate) + "%")
c2.metric(label="분류 예측 구간", value=str(pred_class + 1) + "구간 (" + str(low_edge) + "% ~ " + str(high_edge) + "%)")

actual_rows = region_df[region_df["연도"] == target_year]
if not actual_rows.empty:
    actual_val = actual_rows[metric_option].values[0]
    c3.metric(label="실제 관측값", value=str(actual_val) + "%")
else:
    c3.metric(label="데이터 구분", value="미래 예측치")

st.subheader("연도별 출생률 그래프 (입력 연도 빨간색 표시)")

actual_chart = region_df[["연도", metric_option]].rename(columns={metric_option: "기존 출생률(%)"})
user_chart = pd.DataFrame({"연도": [target_year], "사용자 입력 예측값(%)": [predicted_rate]})

merged = pd.merge(actual_chart, user_chart, on="연도", how="outer").sort_values("연도")
merged["연도"] = merged["연도"].astype(str)

st.scatter_chart(
    data=merged,
    x="연도",
    y=["기존 출생률(%)", "사용자 입력 예측값(%)"],
    color=["#1f77b4", "#FF0000"],
    size=150,
    height=450,
)

st.caption("파란색: 기존 데이터(2016~2025) / 빨간색: 사용자 입력 연도 예측값")

with st.expander("상세 데이터 보기"):
    st.dataframe(region_df, use_container_width=True)
