import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

# 1. 페이지 설정
st.set_page_config(
    page_title="서울 파인다이닝 1박 2일 미식 여행",
    page_icon="🍽️",
    layout="wide"
)

# 2. 파인다이닝 장소 데이터 정의
locations_data = [
    {
        "day": "1일차 (점심)",
        "name": "콘피에르 파인다이닝",
        "category": "모던 한식 컨템퍼러리",
        "lat": 37.5665,
        "lng": 126.9780,
        "description": "합리적인 가격대에 감각적인 코스 요리를 선보이며, 첫 미식 여행의 포문을 열기에 훌륭한 파인다이닝입니다."
    },
    {
        "day": "1일차 (저녁)",
        "name": "정식당",
        "category": "뉴 코리안 미쉐린 2스타",
        "lat": 37.5264,
        "lng": 127.0396,
        "description": "한국의 전통 재료를 현대적이고 창의적인 분자 가스트로놀로지로 재해석하여 전 세계 미식가들을 매료시키는 명소입니다."
    },
    {
        "day": "2일차 (점심)",
        "name": "서울다이닝",
        "category": "유러피안 컨템퍼러리",
        "lat": 37.5559,
        "lng": 127.0012,
        "description": "남산 주변의 쾌적한 뷰와 함께 깊이 있는 유러피안 베이스의 감각적인 파인 다이닝 코스를 즐길 수 있습니다."
    },
    {
        "day": "2일차 (저녁)",
        "name": "소울다이닝",
        "category": "파인 다이닝 / 한식",
        "lat": 37.5400,
        "lng": 126.9850,
        "description": "해방촌 언덕에 위치해 아늑한 분위기 속에서 한국의 정취를 담은 창의적인 파인다이닝 디너를 경험할 수 있습니다."
    }
]

df = pd.DataFrame(locations_data)

# 3. 타이틀 및 소개
st.title("🍽️ 서울 파인다이닝 1박 2일 미식 여행 코스")
st.markdown("세계적인 미식가들과 여행객들이 극찬하는 서울의 대표 파인다이닝 레스토랑들을 엄선한 1박 2일 코스입니다.")

# 4. 지도 생성 함수
def create_map():
    # 서울 중심부 좌표
    seoul_center = [37.5520, 126.9850]
    m = folium.Map(location=seoul_center, zoom_start=13, tiles="OpenStreetMap")
    
    # 마커 추가
    for idx, row in df.iterrows():
        popup_html = f"""
        <div style="width:220px">
            <h4 style="margin-bottom:5px;"><b>{row['name']}</b></h4>
            <p style="font-size:12px; color:gray; margin-bottom:5px;">{row['day']} | {row['category']}</p>
            <p style="font-size:13px;">{row['description']}</p>
        </div>
        """
        
        folium.Marker(
            location=[row['lat'], row['lng']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{row['day']}: {row['name']}",
            icon=folium.Icon(color="purple" if "1일차" in row['day'] else "orange", icon="cutlery", prefix="fa")
        ).add_to(m)
        
    return m

# 5. 지도 화면 출력
st.subheader("🗺️ 미식 여행 동선 지도")
st.caption("📍 마커를 클릭하면 각 식당의 상세한 일정과 코스 설명을 확인할 수 있습니다.")

map_obj = create_map()
st_folium(map_obj, width="100%", height=500)

st.markdown("---")

# 6. 지도 밑 관광지(식당) 설명 섹션
st.subheader("📌 1박 2일 파인다이닝 일정 상세 보기")

col1, col2 = st.columns(2)

for idx, row in df.iterrows():
    target_col = col1 if idx % 2 == 0 else col2
    with target_col:
        with st.expander(f"**{row['day']}** : {row['name']} ({row['category']})", expanded=True):
            st.write(row['description'])
            st.caption(f"📍 위치 좌표: 위도 {row['lat']}, 경도 {row['lng']}")
