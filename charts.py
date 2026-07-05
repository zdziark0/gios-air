from __future__ import annotations
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
WEEKDAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
WEEKDAY_PL = {'Monday': 'pon', 'Tuesday': 'wt', 'Wednesday': 'śr', 'Thursday': 'czw', 'Friday': 'pt', 'Saturday': 'sob', 'Sunday': 'niedz'}

def map_stations(stations: pd.DataFrame, values: pd.DataFrame | None=None):
    df = stations.copy()
    color_col = None
    if values is not None and (not values.empty):
        agg = values.groupby('station_id', as_index=False)['value'].mean().rename(columns={'value': 'avg_value'})
        df = df.merge(agg, on='station_id', how='left')
        color_col = 'avg_value'
    fig = px.scatter_map(df, lat='lat', lon='lon', color=color_col, hover_name='station_name', hover_data={'city': True, 'lat': False, 'lon': False}, color_continuous_scale='YlOrRd', zoom=5, height=520)
    fig.update_layout(map_style='carto-positron', margin=dict(l=0, r=0, t=30, b=0), title='Stacje pomiarowe — średnie stężenie w wybranym okresie', coloraxis_colorbar_title='µg/m³')
    return fig

def line_over_time(df: pd.DataFrame, param: str):
    daily = df.groupby(['day', 'station_name'], as_index=False)['value'].mean()
    fig = px.line(daily, x='day', y='value', color='station_name', markers=False, title=f'{param} — średnie dobowe stężenie w czasie', labels={'day': 'Data', 'value': 'Stężenie [µg/m³]', 'station_name': 'Stacja'})
    _apply_norm_line(fig, df)
    fig.update_layout(hovermode='x unified', height=420)
    return fig

def bar_ranking(df: pd.DataFrame, param: str, top: int=15):
    agg = df.groupby('station_name', as_index=False)['value'].mean().sort_values('value', ascending=False).head(top)
    fig = px.bar(agg, x='value', y='station_name', orientation='h', color='value', color_continuous_scale='YlOrRd', title=f'{param} — ranking najbardziej zanieczyszczonych stacji', labels={'value': 'Śr. stężenie [µg/m³]', 'station_name': ''})
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=460, coloraxis_showscale=False)
    return fig

def box_by_city(df: pd.DataFrame, param: str):
    fig = px.box(df, x='city', y='value', color='city', points='outliers', title=f'{param} — rozkład stężeń wg miasta', labels={'city': 'Miasto', 'value': 'Stężenie [µg/m³]'})
    fig.update_layout(showlegend=False, height=420)
    return fig

def histogram(df: pd.DataFrame, param: str):
    fig = px.histogram(df, x='value', nbins=40, title=f'{param} — histogram rozkładu pomiarów', labels={'value': 'Stężenie [µg/m³]', 'count': 'Liczba pomiarów'}, color_discrete_sequence=['#d94801'])
    fig.update_layout(bargap=0.05, height=380, showlegend=False)
    return fig

def heatmap_hour_weekday(df: pd.DataFrame, param: str):
    piv = df.groupby(['weekday', 'hour'], as_index=False)['value'].mean().pivot(index='weekday', columns='hour', values='value')
    piv = piv.reindex([d for d in WEEKDAY_ORDER if d in piv.index])
    piv.index = [WEEKDAY_PL.get(d, d) for d in piv.index]
    fig = px.imshow(piv, aspect='auto', color_continuous_scale='YlOrRd', title=f'{param} — średnie stężenie: godzina × dzień tygodnia', labels={'x': 'Godzina', 'y': 'Dzień', 'color': 'µg/m³'})
    fig.update_layout(height=360)
    return fig

def scatter_daily(df: pd.DataFrame, param: str):
    sample = df.sample(min(len(df), 3000), random_state=1) if len(df) > 3000 else df
    fig = px.scatter(sample, x='hour', y='value', color='value', color_continuous_scale='YlOrRd', opacity=0.5, title=f'{param} — dobowy profil stężeń (rozrzut godzinowy)', labels={'hour': 'Godzina doby', 'value': 'Stężenie [µg/m³]'})
    fig.update_layout(height=400, coloraxis_showscale=False)
    return fig

def _apply_norm_line(fig, df: pd.DataFrame):
    norm = df['norm'].dropna().iloc[0] if 'norm' in df and df['norm'].notna().any() else None
    if norm:
        fig.add_hline(y=norm, line_dash='dash', line_color='red', annotation_text=f'norma {norm:.0f} µg/m³', annotation_position='top left')
