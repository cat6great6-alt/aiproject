import platform
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# 1. 페이지 기본 설정
st.set_page_config(page_title="서울 월별 기온 분석", layout="wide")


# 2. 한글 폰트 깨짐 방지 설정
def set_korean_font():
    system_name = platform.system()
    if system_name == "Windows":
        plt.rcParams["font.family"] = "Malgun Gothic"
    elif system_name == "Darwin":  # macOS
        plt.rcParams["font.family"] = "AppleGothic"
    else:  # Linux (Streamlit Cloud 등)
        # 나눔고딕 폰트가 설치되어 있는 경우 적용
        font_list = [f.name for f in fm.fontManager.ttflist]
        if "NanumGothic" in font_list:
            plt.rcParams["font.family"] = "NanumGothic"
        else:
            plt.rcParams["font.family"] = "DejaVu Sans"

    # 마이너스 기호(-) 깨짐 방지
    plt.rcParams["axes.unicode_minus"] = False


set_korean_font()


# 3. 데이터 로드 및 전처리 함수 (캐싱 적용으로 속도 향상)
@st.cache_data
def load_data(file_path):
    # 기상청 데이터 인코딩(cp949) 및 상단 메타데이터(11줄) 건너뛰기
    try:
        df = pd.read_csv(file_path, skiprows=11, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, skiprows=11, encoding="utf-8-sig")

    # 컬럼명 앞뒤 공백 및 탭 문자 제거
    df.columns = df.columns.str.strip()

    # '일시' 컬럼에서 연도(int)와 월(int) 분리
    df["일시"] = df["일시"].astype(str).str.strip()
    df = df[df["일시"].str.contains("-", na=False)].copy()
    df["연도"] = df["일시"].str.split("-").str[0].astype(int)
    df["월"] = df["일시"].str.split("-").str[1].astype(int)

    # 기온 데이터 숫자형 변환
    df["최고기온(℃)"] = pd.to_numeric(df["최고기온(℃)"], errors="coerce")
    df["최저기온(℃)"] = pd.to_numeric(df["최저기온(℃)"], errors="coerce")

    return df


# 4. 메인 화면 UI 구성
st.title("🌡️ 서울 기온 데이터 분석 대시보드")

# 파일 경로 지정 (또는 파일 업로더 사용 가능)
DEFAULT_FILE = "extremum_20261109105046.csv"
uploaded_file = st.sidebar.file_uploader(
    "CSV 파일 업로드 (미업로드 시 기본 파일 사용)", type=["csv"]
)

try:
    target_file = uploaded_file if uploaded_file is not None else DEFAULT_FILE
    df = load_data(target_file)

    # 사이드바에서 월 선택 (1월 ~ 12월)
    selected_month = st.sidebar.selectbox(
        "분석할 월을 선택하세요", options=list(range(1, 13)), format_func=lambda x: f"{x}월"
    )

    # 선택한 월의 데이터 필터링 및 연도순 정렬
    filtered_df = df[df["월"] == selected_month].sort_values("연도")

    # 5. Matplotlib 꺾은선 그래프 생성
    fig, ax = plt.subplots(figsize=(12, 5))

    # 최고기온: 핫핑크 (hotpink)
    ax.plot(
        filtered_df["연도"],
        filtered_df["최고기온(℃)"],
        color="hotpink",
        marker="o",
        markersize=4,
        linewidth=1.8,
        label="최고기온(℃)",
    )

    # 최저기온: 하늘색 (skyblue)
    ax.plot(
        filtered_df["연도"],
        filtered_df["최저기온(℃)"],
        color="skyblue",
        marker="o",
        markersize=4,
        linewidth=1.8,
        label="최저기온(℃)",
    )

    # 그래프 제목, 축 라벨, 범례 설정
    ax.set_title("월별 기온분석", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("연도", fontsize=12)
    ax.set_ylabel("온도", fontsize=12)
    ax.legend(loc="best", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.5)

    # Streamlit 화면에 그래프 출력
    st.subheader(f"📅 {selected_month}월 연도별 최고·최저 기온 추이")
    st.pyplot(fig)

    # 데이터 요약 지표 및 원본 표 표시
    col1, col2 = st.columns(2)
    with col1:
        max_row = filtered_df.loc[filtered_df["최고기온(℃)"].idxmax()]
        st.metric(
            label=f"{selected_month}월 역대 최고기온",
            value=f"{max_row['최고기온(℃)']} ℃",
            delta=f"{int(max_row['연도'])}년 관측",
        )
    with col2:
        min_row = filtered_df.loc[filtered_df["최저기온(℃)"].idxmin()]
        st.metric(
            label=f"{selected_month}월 역대 최저기온",
            value=f"{min_row['최저기온(℃)']} ℃",
            delta=f"{int(min_row['연도'])}년 관측",
            delta_color="inverse",
        )

    with st.expander("선택된 월의 상세 데이터 보기"):
        st.dataframe(
            filtered_df[
                ["연도", "월", "평균기온(℃)", "최고기온(℃)", "최고기온일자", "최저기온(℃)", "최저기온일자"]
            ],
            use_container_width=True,
        )

except FileNotFoundError:
    st.error(
        f"'{DEFAULT_FILE}' 파일을 찾을 수 없습니다. 같은 폴더에 파일을 두거나 왼쪽 사이드바에서 CSV 파일을 업로드해주세요."
    )
except Exception as e:
    st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
