from __future__ import annotations
import pandas as pd
import streamlit as st
import gios_api as api
import data_prep as dp
import charts
st.set_page_config(page_title='Jakość powietrza w Polsce — GIOŚ', page_icon='🌫️', layout='wide')

@st.cache_data(ttl=3600, show_spinner='Ładuję stacje…')
def load_stations() -> pd.DataFrame:
    raw = api.fetch_stations()
    return dp.clean_stations(raw)

@st.cache_data(ttl=1800, show_spinner=False)
def load_station_series(station_id: int, station_name: str, city: str, param_code: str) -> pd.DataFrame:
    sensors = api.fetch_sensors(station_id)
    if sensors.empty:
        return pd.DataFrame()
    match = sensors[sensors['param_code'] == param_code]
    if match.empty:
        return pd.DataFrame()
    sensor_id = int(match.iloc[0]['sensor_id'])
    raw = api.fetch_measurements(sensor_id)
    clean = dp.clean_measurements(raw, param_code)
    if clean.empty:
        return clean
    clean['station_id'] = station_id
    clean['station_name'] = station_name
    clean['city'] = city
    return clean
st.title('🌫️ Jakość powietrza w Polsce')
st.caption('Dane: Główny Inspektorat Ochrony Środowiska (GIOŚ) — Państwowy Monitoring Środowiska. Pomiary godzinowe, jednostka µg/m³.')
try:
    stations = load_stations()
except Exception as exc:
    st.error(f'Nie udało się pobrać listy stacji z API GIOŚ. Spróbuj odświeżyć za chwilę.\n\nSzczegóły: {exc}')
    st.stop()
if stations.empty:
    st.warning('API GIOŚ nie zwróciło żadnych stacji.')
    st.stop()
st.sidebar.header('⚙️ Filtry')
param_code = st.sidebar.selectbox('Zanieczyszczenie', options=list(dp.NORMS.keys()), index=0, help='Norma dobowa/średnia dla wybranego wskaźnika naniesiona na wykresy.')
provinces = sorted(stations['province'].dropna().unique().tolist())
sel_prov = st.sidebar.multiselect('Województwo', options=provinces, default=provinces[:3] if len(provinces) >= 3 else provinces)
prov_df = stations[stations['province'].isin(sel_prov)] if sel_prov else stations
station_labels = prov_df.sort_values('station_name')['label'].tolist()
default_stations = station_labels[:min(6, len(station_labels))]
sel_labels = st.sidebar.multiselect('Stacje pomiarowe', options=station_labels, default=default_stations, help='Wybierz do kilku stacji, żeby porównać.')
sel_stations = prov_df[prov_df['label'].isin(sel_labels)]
max_days = st.sidebar.slider('Zakres — ostatnie dni', min_value=1, max_value=3, value=3, help='API GIOŚ udostępnia pomiary z ostatnich ~3 dób.')
st.sidebar.markdown('---')
st.sidebar.caption(f'Wybrano **{len(sel_stations)}** stacji · parametr **{param_code}**')
if sel_stations.empty:
    st.info('Wybierz co najmniej jedną stację w panelu po lewej.')
    st.stop()
frames = []
progress = st.progress(0.0, text='Pobieram pomiary…')
rows = list(sel_stations.itertuples(index=False))
for i, row in enumerate(rows):
    frames.append(load_station_series(row.station_id, row.station_name, row.city, param_code))
    progress.progress((i + 1) / len(rows))
progress.empty()
data = dp.combine_station_data(frames)
if data.empty:
    st.warning(f'Brak pomiarów **{param_code}** dla wybranych stacji (nie każda stacja mierzy każdy wskaźnik). Zmień parametr albo dobierz inne stacje.')
    st.stop()
if not data.empty:
    cutoff = data['date'].max() - pd.Timedelta(days=max_days)
    data = data[data['date'] >= cutoff]
kpi = dp.summarize(data)
norm = dp.NORMS.get(param_code)
c1, c2, c3, c4 = st.columns(4)
c1.metric('Średnie stężenie', dp.format_pl_number(kpi['avg'], 'µg/m³'))
c2.metric('Maksimum', dp.format_pl_number(kpi['max'], 'µg/m³'))
c3.metric('Przekroczenia normy', f'{kpi['exceedances']}', help=f'Liczba pomiarów powyżej normy ({norm:.0f} µg/m³).' if norm else None)
c4.metric('Liczba pomiarów', f'{kpi['count']:,}'.replace(',', ' '))
st.markdown('---')
tab_map, tab_trend, tab_rank, tab_dist = st.tabs(['🗺️ Mapa', '📈 Trendy', '🏆 Rankingi', '📊 Rozkłady'])
with tab_map:
    st.subheader('Rozmieszczenie stacji')
    st.plotly_chart(charts.map_stations(sel_stations, data), use_container_width=True)
    st.caption('Kolor punktu odpowiada średniemu stężeniu wybranego wskaźnika w analizowanym okresie — im ciemniejszy, tym gorzej.')
with tab_trend:
    st.subheader('Zmiany w czasie')
    st.plotly_chart(charts.line_over_time(data, param_code), use_container_width=True)
    st.caption('Przerywana czerwona linia to poziom normy. Skoki zwykle pokrywają się z godzinami szczytu i wieczorem.')
with tab_rank:
    st.subheader('Ranking stacji')
    st.plotly_chart(charts.bar_ranking(data, param_code), use_container_width=True)
    st.caption('Ranking wg średniego stężenia w wybranym okresie. Pozwala szybko wskazać najbardziej obciążone lokalizacje.')
with tab_dist:
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(charts.box_by_city(data, param_code), use_container_width=True)
    with col_b:
        st.plotly_chart(charts.histogram(data, param_code), use_container_width=True)
    st.plotly_chart(charts.heatmap_hour_weekday(data, param_code), use_container_width=True)
    st.caption('Heatmapa pokazuje dobowo-tygodniowy wzorzec: ciemniejsze pola to godziny/dni z wyższym zanieczyszczeniem.')
    st.plotly_chart(charts.scatter_daily(data, param_code), use_container_width=True)
with st.expander('🔎 Podgląd danych (po czyszczeniu)'):
    st.dataframe(data[['date', 'station_name', 'city', 'value', 'exceeded']].sort_values('date', ascending=False).head(500), use_container_width=True)
st.markdown('---')
st.caption('Źródło: GIOŚ / Państwowy Monitoring Środowiska. Dane niezweryfikowane, mogą ulec zmianie.')
