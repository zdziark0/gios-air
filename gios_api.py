from __future__ import annotations
import time
import requests
import pandas as pd
import streamlit as st
BASE_V1 = 'https://api.gios.gov.pl/pjp-api/v1/rest'
BASE_LEGACY = 'https://api.gios.gov.pl/pjp-api/rest'
HEADERS = {'Accept': 'application/json, application/ld+json, */*', 'User-Agent': 'gios-air-dashboard/1.0'}
TIMEOUT = 20

def _get(url: str, params: dict | None=None, retries: int=3) -> dict:
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(1.2 * (attempt + 1))
    raise RuntimeError(f'Nie udało się pobrać danych z {url}: {last_exc}')

def _get_with_fallback(path_v1: str, path_legacy: str, params: dict | None=None) -> dict:
    try:
        return _get(f'{BASE_V1}{path_v1}', params=params)
    except RuntimeError:
        return _get(f'{BASE_LEGACY}{path_legacy}')

@st.cache_data(ttl=3600, show_spinner='Pobieram listę stacji pomiarowych…')
def fetch_stations() -> pd.DataFrame:
    rows: list[dict] = []
    page = 0
    size = 500
    while True:
        try:
            data = _get(f'{BASE_V1}/station/findAll', params={'size': size, 'page': page})
        except RuntimeError:
            data = _get(f'{BASE_LEGACY}/station/findAll')
            rows = _unwrap_list(data)
            break
        items = _unwrap_list(data)
        if not items:
            break
        rows.extend(items)
        total_pages = _total_pages(data)
        page += 1
        if total_pages is not None and page >= total_pages:
            break
        if total_pages is None and len(items) < size:
            break
    return _normalize_stations(rows)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_sensors(station_id: int) -> pd.DataFrame:
    data = _get_with_fallback(f'/station/sensors/{station_id}', f'/station/sensors/{station_id}')
    items = _unwrap_list(data)
    rows = []
    for it in items:
        param = it.get('param') or {}
        rows.append({'sensor_id': it.get('id') or it.get('Identyfikator stanowiska'), 'param_name': param.get('paramName') or it.get('Wskaźnik') or it.get('Nazwa wskaźnika'), 'param_code': param.get('paramCode') or it.get('Wskaźnik - kod') or it.get('Kod wskaźnika')})
    return pd.DataFrame(rows).dropna(subset=['sensor_id'])

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_measurements(sensor_id: int) -> pd.DataFrame:
    data = _get_with_fallback(f'/data/getData/{sensor_id}', f'/data/getData/{sensor_id}')
    items = _unwrap_list(data)
    rows = []
    for it in items:
        d = it.get('date') or it.get('Data')
        v = it.get('value') if 'value' in it else it.get('Wartość')
        rows.append({'date': d, 'value': v})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    return df.dropna(subset=['date']).sort_values('date')

def _unwrap_list(data) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ('Lista stacji pomiarowych', 'Lista stanowisk pomiarowych', 'Lista danych pomiarowych', 'values', 'data'):
            if key in data and isinstance(data[key], list):
                return data[key]
        for v in data.values():
            if isinstance(v, list):
                return v
    return []

def _total_pages(data) -> int | None:
    if isinstance(data, dict):
        for key in ('totalPages', 'Liczba stron', 'pageCount'):
            if key in data:
                try:
                    return int(data[key])
                except (TypeError, ValueError):
                    return None
    return None

def _normalize_stations(rows: list[dict]) -> pd.DataFrame:
    out = []
    for it in rows:
        city_obj = it.get('city') or {}
        commune_obj = city_obj.get('commune') or {}
        out.append({'station_id': it.get('id') or it.get('Identyfikator stacji'), 'station_name': it.get('stationName') or it.get('Nazwa stacji'), 'lat': it.get('gegrLat') or it.get('WGS84 φ N'), 'lon': it.get('gegrLon') or it.get('WGS84 λ E'), 'city': (city_obj.get('name') if city_obj else None) or it.get('Nazwa miasta'), 'commune': commune_obj.get('communeName') or it.get('Gmina'), 'district': commune_obj.get('districtName') or it.get('Powiat'), 'province': commune_obj.get('provinceName') or it.get('Województwo')})
    df = pd.DataFrame(out)
    return df
