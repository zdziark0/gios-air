from __future__ import annotations
import numpy as np
import pandas as pd
NORMS = {'PM10': 50.0, 'PM2.5': 25.0, 'NO2': 200.0, 'SO2': 125.0, 'O3': 120.0, 'C6H6': 5.0, 'CO': 10000.0}

def clean_stations(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    for col in ('lat', 'lon'):
        df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['station_id'] = pd.to_numeric(df['station_id'], errors='coerce')
    df = df.dropna(subset=['station_id', 'lat', 'lon'])
    df['station_id'] = df['station_id'].astype(int)
    for col in ('city', 'province', 'district', 'commune'):
        if col in df.columns:
            df[col] = df[col].fillna('brak danych').str.strip()
    df['label'] = df['station_name'].fillna('') + ' (' + df['city'] + ')'
    df = df.drop_duplicates(subset=['station_id']).reset_index(drop=True)
    return df

def clean_measurements(df: pd.DataFrame, param_code: str) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.dropna(subset=['date'])
    df = df.sort_values('date')
    df['value'] = df['value'].interpolate(limit=2, limit_direction='both')
    df = df.dropna(subset=['value'])
    df['hour'] = df['date'].dt.hour
    df['weekday'] = df['date'].dt.day_name()
    df['day'] = df['date'].dt.date
    df['param'] = param_code
    norm = NORMS.get(param_code)
    df['exceeded'] = df['value'] > norm if norm else False
    df['norm'] = norm
    return df.reset_index(drop=True)

def combine_station_data(frames: list[pd.DataFrame]) -> pd.DataFrame:
    frames = [f for f in frames if f is not None and (not f.empty)]
    if not frames:
        return pd.DataFrame(columns=['date', 'value', 'hour', 'weekday', 'day', 'param', 'exceeded', 'norm', 'station_name', 'city'])
    return pd.concat(frames, ignore_index=True)

def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {'avg': np.nan, 'max': np.nan, 'exceedances': 0, 'count': 0}
    return {'avg': float(df['value'].mean()), 'max': float(df['value'].max()), 'exceedances': int(df['exceeded'].sum()), 'count': int(len(df))}

def format_pl_number(x: float, unit: str='') -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return '—'
    s = f'{x:,.1f}'.replace(',', ' ').replace('.', ',')
    return f'{s} {unit}'.strip()
