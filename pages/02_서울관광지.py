streamlit
folium
streamlit-folium
pandasimport streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="외국인이 사랑하는 서울 관광지 TOP 10",
    page_icon="🗽",
    layout="wide"
)

# 2. 데이터 정의 (서울 주요 관광지 TOP 10)
locations_data = [
    {
        "rank": 1,
        "name": "경복궁",
        "category": "역사 / 문화",
        "lat": 37.5796,
        "lng": 126.9770,
        "description": "조선 왕조의 으뜸 궁궐로, 한복 체험과 왕궁 수문장 교식 의식이 외국인 관광객에게 매우 높은 인기를 끌고 있습니다.",
        "icon": "bank"
    },
    {
        "rank": 2,
        "name": "N서울타워 (남산타워)",
        "category": "랜드마크 / 야경",
        "lat": 37.5512,
        "lng": 126.9882,
        "description": "서울 도심 전경과 밤경치를 한눈에 조망할 수 있는 대표 랜드마크이며, 사랑의 자물쇠 명소로도 nổi 명합니다.",
        "icon": "camera"
    },
    {
        "rank": 3,
        "name": "명동 쇼핑거리",
        "category": "쇼핑 / 길거리 음원",
        "lat": 37.5636,
        "lng": 126.9860,
        "description": "K-뷰티 숍, 패션 브랜드, 다양하고 맛있는 한국 길거리 음식을 한곳에서 만날 수 있는 필수 쇼핑 코스입니다.",
        "icon": "shopping-cart"
    },
    {
        "rank": 4,
        "name": "북촌한옥마을",
        "category": "전통 문화",
        "lat": 37.5826,
        "lng": 126.9831,
        "description": "경복궁과 창덕궁 사이에 위치한 전통 한옥 주거지로, 고즈넉한 기와지붕 골목을 배경으로 인생샷을 남기기 좋습니다.",
        "icon": "home"
    },
    {
        "rank": 5,
        "name": "홍대 거리",
        "category": "청춘 / 문화 / 쇼핑",
        "lat": 37.5567,
        "lng": 126.9237,
        "description": "버스킹 공연, 트렌디한 카페, 아기자기한 숍, 활기찬 야간 유흥 문화를 경험할 수 있는 젊음의 거리입니다.",
        "icon": "music"
    },
    {
        "rank": 6,
        "name": "광장시장",
        "category": "전통시장 / K-푸드",
        "lat": 37.5701,
        "lng": 126.9998,
        "description": "100년 전통의 시장으로 빈대떡, 육회, 마약김밥 등 한국의 푸짐하고 생생한 시장 음식을 맛볼 수 있습니다.",
        "icon": "cutlery"
    },
    {
        "rank": 7,
        "name": "동대문디자인플라자 (DDP)",
        "category": "건축 / 패션",
        "lat": 37.5665,
        "lng": 127.0090,
        "description": "세계적인 건축가 자하 하디드가 설계한 곡선미 넘치는 미래형 복합문화공간이자 서울 패션의 중심지입니다.",
        "icon": "cube"
    },
    {
        "rank": 8,
        "name": "창덕궁 & 후원",
        "category": "세계문화유산",
        "lat": 37.5794,
        "lng": 126.9910,
        "description": "유네스코 세계문화유산으로 지정된 궁궐로, 한국의 전통 정원 양식을 완벽하게 보존하고 있는 '비원(후원)'이 유명합니다.",
        "icon": "leaf"
    },
    {
        "rank": 9,
        "name": "롯데월드타워 & 석촌호수",
        "category": "현대 랜드마크",
        "lat": 37.5126,
        "lng": 127.1025,
        "description": "국내 최고층(123층, 555m) 건물로 초고층 전망대 '서울스카이'와 석촌호수 산책로를 함께 즐길 수 있습니다.",
        "icon": "star"
    },
    {
        "rank": 10,
        "name": "인사동",
        "category": "전통 공예 / 찻집",
        "lat": 37.5744,
        "lng": 126.9849,
        "description": "한국 전통 골동품, 도자기, 한지, 전통차 등을 만날 수 있는 전통 문화 거리로 쌈지길이 대표적입니다.",
        "icon": "gift"
    }
]

df = pd.DataFrame(locations_data)

# 3. 화면 타이틀
st.title("🗽 외국인이 사랑하는 서울 주요 관광지 TOP 10")
st.markdown("서울을 찾는 외국인 관광객들에게 가장 많은 사랑을 받는 대표 명소 10곳을 지도와 함께 살펴보세요.")

# 4. 지도 생성 함수
def create_map():
    # 서울 중심부 좌표 (위도, 경도)
    seoul_center = [37.5665, 126.9780]
    
    # Folium 지도 객체 생성 (초기 줌 레벨 12)
    m = folium.Map(location=seoul_center, zoom_start=12, tiles="OpenStreetMap")
    
    # 관광지 마커 추가
    for idx, row in df.iterrows():
        popup_html = f"""
        <div style="width:200px">
            <h4 style="margin-bottom:5px;"><b>{row['rank']}. {row['name']}</b></h4>
            <p style="font-size:12px; color:gray; margin-bottom:8px;">{row['category']}</p>
            <p style="font-size:13px;">{row['description']}</p>
        </div>
        """
        
        folium.Marker(
            location=[row['lat'], row['lng']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{row['rank']}위: {row['name']}",
            icon=folium.Icon(color="red" if row['rank'] <= 3 else "blue", icon="info-sign")
        ).add_to(m)
        
    return m

# 5. 지도 레이아웃 출력
st.subheader("🗺️ 서울 관광 명소 지도")
st.caption("📍 마커를 클릭하시면 해당 관광지의 간략한 정보를 확인할 수 있습니다.")

# Streamlit 지도 렌더링 (화면 너비에 맞게 조절)
map_obj = create_create_map() if 'create_create_map' in locals() else create_map()
st_folium(map_obj, width="100%", height=500)

st.markdown("---")

# 6. 하단 상세 설명 섹션 (카드 스타일)
st.subheader("📌 TOP 10 관광지 상세 설명")

# 2열(Column)로 배치하여 직관적으로 구성
col1, col2 = st.columns(2)

for idx, row in df.iterrows():
    # 홀수번은 col1, 짝수번은 col2에 배치
    target_col = col1 if idx % 2 == 0 else col2
    
    with target_col:
        with st.expander(f"**{row['rank']}위. {row['name']}** ({row['category']})", expanded=True):
            st.write(row['description'])
            st.caption(f"🌐 위도: {row['lat']} / 경도: {row['lng']}")
