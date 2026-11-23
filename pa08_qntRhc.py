import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib  # Streamlit Cloud 리눅스 환경 한글 깨짐 방지
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris

# 페이지 기본 설정
st.set_page_config(page_title="붓꽃(Iris) 품종 예측기", page_icon="🌸", layout="centered")

st.title("🌸 붓꽃(Iris) 품종 예측 및 위치 시각화")
st.write("꽃잎 길이와 꽃잎 너비를 입력하면 **랜덤 포레스트(Random Forest)** 분류 모델이 품종을 예측하고, 전체 데이터 분포에서 입력값의 위치를 표시합니다.")

# 1. 데이터 로드 (캐싱 적용)
@st.cache_data
def load_data():
    file_name = "l1i2li121li2l1i.xlsx"
    if os.path.exists(file_name):
        df = pd.read_excel(file_name, sheet_name="Iris")
        if "Unnamed: 0" in df.columns:
            df = df.drop(columns=["Unnamed: 0"])
        return df
    else:
        # 파일이 없을 경우 동일 구조의 기본 Iris 데이터셋 로드
        iris = load_iris()
        df = pd.DataFrame(iris.data, columns=["꽃받침 길이", "꽃받침 너비", "꽃잎 길이", "꽃잎너비"])
        df["품종"] = [f"Iris-{iris.target_names[i]}" for i in iris.target]
        return df

df = load_data()

# 2. 모델 학습 (캐싱 적용)
@st.cache_resource
def train_model(data):
    X = data[["꽃잎 길이", "꽃잎너비"]]
    y = data["품종"]
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

model = train_model(df)

# 데이터 최솟값 / 최댓값 계산
min_len, max_len = float(df["꽃잎 길이"].min()), float(df["꽃잎 길이"].max())
min_wid, max_wid = float(df["꽃잎너비"].min()), float(df["꽃잎너비"].max())

# 3. 사용자 입력 영역 및 입력 가능 범위 안내
st.subheader("1. 꽃잎 수치 입력")
st.info(
    f"📌 **입력 가능한 값의 범위 (데이터셋 기준)**\n"
    f"- **꽃잎 길이 (Petal Length):** `{min_len} cm` ~ `{max_len} cm`\n"
    f"- **꽃잎 너비 (Petal Width):** `{min_wid} cm` ~ `{max_wid} cm`"
)

col1, col2 = st.columns(2)
with col1:
    petal_length = st.number_input(
        f"꽃잎 길이 ({min_len} ~ {max_len} cm)",
        min_value=min_len,
        max_value=max_len,
        value=3.8,
        step=0.1,
        format="%.1f"
    )

with col2:
    petal_width = st.number_input(
        f"꽃잎 너비 ({min_wid} ~ {max_wid} cm)",
        min_value=min_wid,
        max_value=max_wid,
        value=1.2,
        step=0.1,
        format="%.1f"
    )

# 4. 품종 예측
input_df = pd.DataFrame([[petal_length, petal_width]], columns=["꽃잎 길이", "꽃잎너비"])
prediction = model.predict(input_df)[0]
proba = model.predict_proba(input_df)[0]
classes = model.classes_

st.subheader("2. 품종 예측 결과")
st.success(f"예측된 품종은 **{prediction}** 입니다!")

# 품종별 예측 확률 표시
proba_df = pd.DataFrame({
    "품종": classes,
    "예측 확률 (%)": [round(p * 100, 1) for p in proba]
})
st.dataframe(proba_df, use_container_width=True, hide_index=True)

# 5. 산점도 시각화 (가로축: 꽃잎 길이, 세로축: 꽃잎 너비, 사용자 입력값: 노란색 별)
st.subheader("3. 데이터 분포 및 사용자 입력 위치")

fig, ax = plt.subplots(figsize=(8, 5))

colors = {
    "Iris-setosa": "#1f77b4",      # 파랑
    "Iris-versicolor": "#2ca02c",  # 초록
    "Iris-virginica": "#d62728"    # 빨강
}

for species, group in df.groupby("품종"):
    ax.scatter(
        group["꽃잎 길이"],
        group["꽃잎너비"],
        label=species,
        color=colors.get(species, "gray"),
        alpha=0.75,
        s=55,
        edgecolors="white",
        linewidth=0.5
    )

# 사용자 입력값을 노란색 별(*)로 표시
ax.scatter(
    petal_length,
    petal_width,
    color="gold",
    marker="*",
    s=380,
    edgecolors="black",
    linewidth=1.3,
    zorder=10,
    label=f"사용자 입력값 ({petal_length}, {petal_width})"
)

ax.set_xlabel("꽃잎 길이 (cm)", fontsize=11)
ax.set_ylabel("꽃잎 너비 (cm)", fontsize=11)
ax.set_title("품종별 꽃잎 길이 vs 꽃잎 너비 분포 및 입력 위치", fontsize=13, pad=12)
ax.grid(True, linestyle="--", alpha=0.4)
ax.legend(loc="upper left", frameon=True)

st.pyplot(fig)
