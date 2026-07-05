JAKOŚĆ POWIETRZA W POLSCE - DASHBOARD GIOŚ

Interaktywna aplikacja analityczna w Streamlit, która pobiera dane o jakości
powietrza z API Głównego Inspektoratu Ochrony Środowiska (GIOŚ) i prezentuje je
w formie dashboardu: mapa stacji, trendy w czasie, rankingi i rozkłady stężeń.

Projekt realizuje pełny przepływ pracy z danymi: pozyskanie, czyszczenie,
analiza, wizualizacja i komunikacja wyników.


DZIAŁAJĄCA WERSJA

https://gios-air-tsdurmfmmnbuyfey8dmgu4.streamlit.app/


CO ROBI APLIKACJA

Pobiera na żywo listę stacji pomiarowych i pomiary z API GIOŚ (bez klucza).
Pozwala filtrować dane wg województwa, stacji, rodzaju zanieczyszczenia
(PM10, PM2.5, NO2, SO2, O3, CO, C6H6) i zakresu czasu.
Liczy KPI: średnie stężenie, maksimum, liczba przekroczeń normy, liczba pomiarów.
Wizualizuje dane na 7 typach wykresów:
  1. Mapa stacji (kolor = poziom zanieczyszczenia)
  2. Wykres liniowy (stężenie w czasie + linia normy)
  3. Słupkowy ranking stacji
  4. Boxplot rozkładu wg miasta
  5. Histogram rozkładu pomiarów
  6. Heatmapa godzina x dzień tygodnia
  7. Scatter - dobowy profil stężeń


ŹRÓDŁO DANYCH

API GIOŚ - portal Jakość Powietrza (Państwowy Monitoring Środowiska):
https://powietrze.gios.gov.pl/pjp/content/api

Wykorzystane endpointy (wersja v1, aktualna od 30.06.2025):
  Lista stacji         /pjp-api/v1/rest/station/findAll
  Stanowiska stacji    /pjp-api/v1/rest/station/sensors/{stationId}
  Dane pomiarowe       /pjp-api/v1/rest/data/getData/{sensorId}

Dane udostępniane w ug/m3, pomiary godzinowe z ostatnich ok. 3 dób.
Dane niezweryfikowane, mogą ulec zmianie.


STRUKTURA PROJEKTU

gios-air/
  app.py            orkiestrator - layout, filtry, KPI, zakładki
  gios_api.py       klient API GIOŚ (cache, retry, obsługa błędów)
  data_prep.py      czyszczenie, typy, braki, kolumny pochodne, normy
  charts.py         funkcje wykresów Plotly
  requirements.txt
  README.md


URUCHOMIENIE LOKALNE

  1. Sklonuj repo
     git clone https://github.com/Zdziark0/gios-air.git
     cd gios-air

  2. Środowisko i zależności
     python -m venv .venv
     source .venv/bin/activate        (Windows: .venv\Scripts\activate)
     pip install -r requirements.txt

  3. Uruchom
     streamlit run app.py

Aplikacja ruszy pod http://localhost:8501


DEPLOYMENT

Wdrożone na Streamlit Community Cloud (share.streamlit.io):
publiczne repo, New app, wybór app.py, Deploy. Brak sekretów -
API GIOŚ nie wymaga klucza.


UWAGI TECHNICZNE

Zapytania do API opakowane w @st.cache_data (TTL) - mniej requestów, szybszy UI.
Klient API ma retry z backoffem i normalizuje niespójny format odpowiedzi;
w razie błędu 406 z endpointu v1 automatycznie sięga po starszą wersję usługi.
Nie każda stacja mierzy każdy wskaźnik - aplikacja obsługuje takie przypadki
komunikatem, zamiast przerywać działanie.


Źródło danych: GIOŚ / Państwowy Monitoring Środowiska.
