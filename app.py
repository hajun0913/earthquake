import streamlit as st
import numpy as np
import joblib

# 1. 페이지 설정을 맨 위에 단 한 번만 선언
st.set_page_config(layout="wide")

def app():
    # 내부 연산에 필요한 라이브러리 로컬 호출
    import pandas as pd
    import folium
    from streamlit_folium import st_folium  

    st.title('🌎 세계 지진 위험도 예측 및 대시보드')
    st.markdown('---')

    # 가상 지진 데이터셋 생성 가속화
    @st.cache_data
    def generate_earthquake_data():
        np.random.seed(42)
        total_records = 6000
        lats = np.random.uniform(20.0, 50.0, total_records)
        lons = np.random.uniform(115.0, 145.0, total_records)
        clusters = np.random.choice([0, 1, 2], size=total_records, p=[0.5, 0.3, 0.2])
        
        df = pd.DataFrame({
            '위도': lats,
            '경도': lons,
            'cluster': clusters,
            '발생일시': pd.date_range(start='2010-01-01', periods=total_records, freq='h')
        })
        risk_map = {0: '안전 (낮음)', 1: '주의 (보통)', 2: '경고 (고위험)'}
        return df, risk_map

    df_new, risk_dict = generate_earthquake_data()

    # 💡 [핵심] 지도가 사라지지 않도록 임시 메모리(Session State) 공간을 만들어 둡니다.
    if 'clicked' not in st.session_state:
        st.session_state.clicked = False

    st.sidebar.header('🛰️ 지진 위험도 분석기')

    # 사용자 위경도 입력
    lat = st.sidebar.number_input('위도 입력 (Latitude):', min_value=-90.0, max_value=90.0, value=35.0000, format="%.4f")
    lon = st.sidebar.number_input('경도 입력 (Longitude):', min_value=-180.0, max_value=180.0, value=129.0000, format="%.4f")

    # 버튼을 누르면 메모리에 "나 버튼 눌렸음!" 하고 저장해 둡니다.
    if st.sidebar.button('위험도 예측 및 지도 갱신'):
        st.session_state.clicked = True

    # 버튼이 눌린 상태라면 화면이 새로고침되어도 이 내부 코드가 계속 유지됩니다!
    if st.session_state.clicked:
        st.subheader('🎯 실시간 위치 분석 결과')
        
        near_df = df_new[
            (df_new['위도'] >= lat - 5) & (df_new['위도'] <= lat + 5) &
            (df_new['경도'] >= lon - 5) & (df_new['경도'] <= lon + 5)
        ]

        if not near_df.empty:
            cluster_ratio = near_df['cluster'].value_counts(normalize=True)
            main_cluster = cluster_ratio.idxmax()
            predicted_risk = risk_dict[main_cluster]
            
            if main_cluster == 2:
                st.error(f"⚠️ 예측 결과: 입력하신 위치 주변의 예상 지진 위험도는 **{predicted_risk}** 입니다. 주의가 필요합니다.")
            elif main_cluster == 1:
                st.warning(f"🔔 예측 결과: 입력하신 위치 주변의 예상 지진 위험도는 **{predicted_risk}** 입니다.")
            else:
                st.success(f"✅ 예측 결과: 입력하신 위치 주변의 예상 지진 위험도는 **{predicted_risk}** 입니다.")

            st.markdown('---')
            st.subheader('🗺️ 인터랙티브 지진 위험도 지도 시각화')
            st.write('마우스로 지도를 조작해도 이제 절대 사라지지 않습니다.')
            
            # Folium 지도 생성
            m = folium.Map(location=[lat, lon], zoom_start=6, tiles="OpenStreetMap")
            colors = {0: '#2ecc71', 1: '#f39c12', 2: '#e74c3c'}

            # 최적화된 렌더링을 위한 데이터 샘플링
            df_sample = df_new.sample(min(len(df_new), 1500), random_state=42)

            for i, row in df_sample.iterrows():
                cls_id = int(row['cluster'])
                folium.CircleMarker(
                    location=[row['위도'], row['경도']],
                    radius=2.5,
                    color=colors.get(cls_id, '#7f8c8d'),
                    fill=True,
                    fill_color=colors.get(cls_id, '#7f8c8d'),
                    fill_opacity=0.6
                ).add_to(m)

            # 표적 위치 마커
            folium.Marker(
                location=[lat, lon],
                icon=folium.Icon(color='black', icon='star', prefix='fa'),
                tooltip=f"📍 예측 타겟 위치 (위도: {lat}, 경도: {lon})"
            ).add_to(m)

            # st_folium을 안전하게 표출 (key값을 주어 컴포넌트를 고정합니다)
            st_folium(m, width='100%', height=550, key="earthquake_map")

        else:
            st.warning("⚠️ 입력하신 위치 주변 5도 이내에 데이터가 없습니다. 다른 좌표를 지정해 보세요.")

    # 사이드바 하단 기본 정보
    st.sidebar.markdown('---')
    st.sidebar.subheader('📊 데이터베이스 정보')
    st.sidebar.write(f"활성 단층 샘플 수: {len(df_new):,} 개")
    st.sidebar.write(f"관측 로그 데이터 타임라인: {df_new['발생일시'].min().year}년 ~ {df_new['발생일시'].max().year}년")

if __name__ == '__main__':
    app()