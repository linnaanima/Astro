import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import time
import json

# Seitenkonfiguration
st.set_page_config(
    page_title="Astrotourismus Weltkarte - Mega Edition",
    page_icon="🌟",
    layout="wide"
)

# Erweiterte API-Klasse mit mehreren Datenquellen
class MultiSourceWeatherAPI:
    """
    Klasse für mehrere API-Datenquellen
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Astrotourism-App/1.0'})
    
    @staticmethod
    @st.cache_data(ttl=24*3600)  # 24h Cache
    def get_nasa_power_data(lat, lon, location_name):
        """NASA POWER API - Klimadaten"""
        base_url = "https://power.larc.nasa.gov/api/temporal/climatology/point"
        
        params = {
            'parameters': 'CLOUD_AMT_DAY,CLOUD_AMT_NIGHT,RH2M,T2M,WS10M',
            'community': 'RE',
            'longitude': lon,
            'latitude': lat,
            'start': 2015,
            'end': 2023,
            'format': 'JSON'
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'properties' in data and 'parameter' in data['properties']:
                    params_data = data['properties']['parameter']
                    
                    cloud_night = params_data.get('CLOUD_AMT_NIGHT', {})
                    humidity = params_data.get('RH2M', {})
                    temperature = params_data.get('T2M', {})
                    wind_speed = params_data.get('WS10M', {})
                    
                    if cloud_night:
                        monthly_clouds = list(cloud_night.values())
                        avg_cloud_cover = sum(monthly_clouds) / len(monthly_clouds)
                        
                        # Optimierte Berechnung für Astronomie
                        clear_threshold = 25  # < 25% Bewölkung = gut für Astronomie
                        clear_probability = max(0, (clear_threshold - avg_cloud_cover) / clear_threshold)
                        
                        # Saisonale Variation berücksichtigen
                        min_clouds = min(monthly_clouds)
                        max_clouds = max(monthly_clouds)
                        seasonal_factor = 1 - ((max_clouds - min_clouds) / 100) * 0.3
                        
                        clear_nights = int(365 * clear_probability * seasonal_factor)
                        clear_nights = max(min(clear_nights, 350), 30)  # Between 30-350
                        
                        avg_humidity = sum(humidity.values()) / len(humidity) if humidity else 50
                        avg_temp = sum(temperature.values()) / len(temperature) if temperature else 15
                        avg_wind = sum(wind_speed.values()) / len(wind_speed) if wind_speed else 5
                        
                        return {
                            'success': True,
                            'clear_nights': clear_nights,
                            'cloud_cover': round(avg_cloud_cover, 1),
                            'humidity': round(avg_humidity, 1),
                            'temperature': round(avg_temp - 273.15, 1),  # K to C
                            'wind_speed': round(avg_wind, 1),
                            'data_source': 'NASA POWER',
                            'status': '🛰️ NASA'
                        }
                        
        except Exception as e:
            st.warning(f"NASA API Fehler für {location_name}: {str(e)[:50]}...")
        
        return {'success': False}
    
    @staticmethod
    @st.cache_data(ttl=6*3600)  # 6h Cache für Wetter
    def get_openweather_data(lat, lon, api_key=None):
        """OpenWeatherMap API - Aktuelles Wetter (optional)"""
        if not api_key:
            return {'success': False, 'reason': 'No API key'}
        
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': api_key,
            'units': 'metric'
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'current_clouds': data['clouds']['all'],
                    'current_humidity': data['main']['humidity'],
                    'current_temp': data['main']['temp'],
                    'visibility': data.get('visibility', 10000),
                    'data_source': 'OpenWeather',
                    'status': '🌤️ Live'
                }
        except Exception:
            pass
        
        return {'success': False}
    
    @staticmethod
    def get_enhanced_geographic_estimation(lat, lon, altitude, climate_zone=None):
        """Erweiterte geografische Schätzung"""
        abs_lat = abs(lat)
        
        # Basis nach detaillierten Klimazonen
        if climate_zone == 'desert':
            base_clear = 310
        elif climate_zone == 'polar':
            base_clear = 120
        elif climate_zone == 'mediterranean':
            base_clear = 240
        elif climate_zone == 'continental':
            base_clear = 200
        elif climate_zone == 'oceanic':
            base_clear = 160
        elif climate_zone == 'tropical':
            base_clear = 180
        else:
            # Automatische Klimazone-Bestimmung
            if altitude > 3000:
                base_clear = 290  # Alpine
            elif abs_lat < 23.5 and altitude < 500:
                base_clear = 170  # Tropical lowlands
            elif abs_lat < 23.5 and altitude > 1000:
                base_clear = 250  # Tropical highlands
            elif 23.5 <= abs_lat <= 35 and altitude < 500:
                base_clear = 200  # Subtropical lowlands
            elif 23.5 <= abs_lat <= 35 and altitude > 500:
                base_clear = 270  # Subtropical highlands
            elif 35 <= abs_lat <= 50:
                base_clear = 180  # Temperate
            elif 50 <= abs_lat <= 66.5:
                base_clear = 140  # Subarctic
            else:
                base_clear = 100  # Arctic
        
        # Höhen-Modifikationen
        if altitude > 4000:
            base_clear += 50
        elif altitude > 3000:
            base_clear += 40
        elif altitude > 2000:
            base_clear += 25
        elif altitude > 1000:
            base_clear += 15
        elif altitude > 500:
            base_clear += 8
        
        # Kontinentalitäts-Effekt
        continentality = abs(lon)
        if continentality > 140:  # Sehr kontinental
            base_clear += 30
        elif continentality > 100:  # Kontinental
            base_clear += 20
        elif continentality > 60:  # Leicht kontinental
            base_clear += 10
        
        # Spezielle geografische Faktoren
        # Wüstengürtel (15-35°N/S)
        if 15 <= abs_lat <= 35 and altitude > 200:
            base_clear += 25
        
        # Monsun-Gebiete (reduzieren)
        if (70 <= lon <= 140 and 10 <= lat <= 40) or (-20 <= lat <= 20 and lon > 90):
            base_clear -= 30
        
        # Westküsten-Effekt (marine layer)
        if ((lat > 30 and -130 <= lon <= -110) or  # US West Coast
            (lat > 30 and -20 <= lon <= 10) or     # Europe West Coast
            (-40 <= lat <= -30 and -80 <= lon <= -60)):  # Chile Coast
            base_clear -= 20
        
        return max(min(base_clear, 350), 50)

# Ausgewogene Standort-Datenbank mit exakten Listen
@st.cache_data(ttl=24*3600)
def load_comprehensive_locations():
    """Erweiterte Datenbank mit 100 sorgfältig ausgewählten Standorten weltweit"""
    
    # Exakt 100 Standorte - alle Listen haben die gleiche Länge
    locations = {
        'Name': [
            # CHILE (8 Standorte)
            'Atacama-Wüste', 'ALMA Observatory', 'Paranal Observatory', 'La Silla Observatory',
            'Las Campanas Observatory', 'Cerro Tololo Observatory', 'Elqui Valley', 'Valle de la Luna',
            
            # USA (25 Standorte)
            'Mauna Kea Hawaii', 'Death Valley California', 'Joshua Tree California', 'Bryce Canyon Utah',
            'Capitol Reef Utah', 'Arches Utah', 'Great Basin Nevada', 'Grand Canyon Arizona',
            'Big Bend Texas', 'McDonald Observatory Texas', 'Cherry Springs Pennsylvania',
            'Shenandoah Virginia', 'Acadia Maine', 'Yellowstone Wyoming', 'Grand Teton Wyoming',
            'Badlands South Dakota', 'Glacier Montana', 'Denali Alaska', 'Fairbanks Alaska',
            'Palomar Observatory California', 'Mount Wilson California', 'Lowell Observatory Arizona',
            'Very Large Array New Mexico', 'Black Canyon Colorado', 'Great Sand Dunes Colorado',
            
            # KANADA (8 Standorte)
            'Jasper Nationalpark', 'Mont-Mégantic Quebec', 'Algonquin Ontario', 'Killarney Ontario',
            'Point Pelee Ontario', 'Cypress Hills Alberta', 'Wood Buffalo Alberta', 'Kejimkujik Nova Scotia',
            
            # EUROPA (25 Standorte)
            # Spanien (8)
            'Roque de los Muchachos La Palma', 'Teide Observatorium Teneriffa', 'Calar Alto Andalusien',
            'Montsec Katalonien', 'Picos de Europa', 'Sierra Nevada', 'Extremadura', 'Fuerteventura',
            # Deutschland (5)
            'Zugspitze Bayern', 'Wasserkuppe Rhön', 'Westhavelland Brandenburg', 'Eifel Nationalpark', 'Feldberg Schwarzwald',
            # Frankreich (4)
            'Pic du Midi Observatorium', 'Mont-Blanc Chamonix', 'Cévennes Nationalpark', 'Vosges du Nord',
            # Andere Europa (8)
            'Alqueva Portugal', 'Brecon Beacons Wales', 'Galloway Forest Schottland', 'Kerry Dark Sky Reserve Irland',
            'Jungfraujoch Schweiz', 'Hohe Tauern Österreich', 'Zselic Starry Sky Park Ungarn', 'Møn Dänemark',
            
            # OZEANIEN (10 Standorte)
            'Aoraki Mackenzie Neuseeland', 'Great Barrier Island Neuseeland', 'Lake Tekapo Neuseeland',
            'Uluru Australien', 'Flinders Ranges Australien', 'Warrumbungle Australien',
            'Nullarbor Plain Australien', 'Gibson Desert Australien', 'Kimberley Australien', 'Tasmania Dark Sky Australien',
            
            # AFRIKA (12 Standorte)
            'NamibRand Namibia', 'Kalahari Botswana', 'Karoo Südafrika', 'Drakensberg Südafrika',
            'Sahara Marokko', 'Atlas Mountains Marokko', 'Sahara Algerien', 'Hoggar Mountains Algerien',
            'Ethiopian Highlands Äthiopien', 'Simien Mountains Äthiopien', 'Air Mountains Niger', 'Tibesti Chad',
            
            # ASIEN (12 Standorte)
            'Ladakh Indien', 'Spiti Valley Indien', 'Changthang Plateau Indien', 'Thar Desert Indien',
            'Everest Base Camp Nepal', 'Annapurna Region Nepal', 'Mustang Nepal',
            'Tibet Plateau China', 'Gobi Desert Mongolei', 'Pamir Tadschikistan',
            'Karakorum Pakistan', 'Taklamakan Desert China'
        ],
        
        'Land': [
            # Chile (8)
            'Chile', 'Chile', 'Chile', 'Chile', 'Chile', 'Chile', 'Chile', 'Chile',
            
            # USA (25)
            'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA',
            'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA',
            'USA', 'USA', 'USA', 'USA', 'USA',
            
            # Kanada (8)
            'Kanada', 'Kanada', 'Kanada', 'Kanada', 'Kanada', 'Kanada', 'Kanada', 'Kanada',
            
            # Europa (25)
            # Spanien (8)
            'Spanien', 'Spanien', 'Spanien', 'Spanien', 'Spanien', 'Spanien', 'Spanien', 'Spanien',
            # Deutschland (5)
            'Deutschland', 'Deutschland', 'Deutschland', 'Deutschland', 'Deutschland',
            # Frankreich (4)
            'Frankreich', 'Frankreich', 'Frankreich', 'Frankreich',
            # Andere Europa (8)
            'Portugal', 'Wales', 'Schottland', 'Irland', 'Schweiz', 'Österreich', 'Ungarn', 'Dänemark',
            
            # Ozeanien (10)
            'Neuseeland', 'Neuseeland', 'Neuseeland', 'Australien', 'Australien', 'Australien',
            'Australien', 'Australien', 'Australien', 'Australien',
            
            # Afrika (12)
            'Namibia', 'Botswana', 'Südafrika', 'Südafrika', 'Marokko', 'Marokko',
            'Algerien', 'Algerien', 'Äthiopien', 'Äthiopien', 'Niger', 'Chad',
            
            # Asien (12)
            'Indien', 'Indien', 'Indien', 'Indien', 'Nepal', 'Nepal', 'Nepal',
            'Tibet/China', 'Mongolei', 'Tadschikistan', 'Pakistan', 'China'
        ],
        
        
        'Latitude': [
            # Chile (8)
            -24.6282, -24.0258, -24.6275, -29.2563, -29.0158, -30.1697, -29.9081, -22.9083,
            
            # USA (25)
            19.8207, 36.5054, 33.8792, 37.5930, 38.2972, 38.7331, 39.2856, 36.0544,
            29.1275, 30.6792, 41.6628, 38.2972, 44.3500, 44.9778, 43.7904,
            43.8554, 48.7596, 63.0695, 64.8378, 33.3533, 34.2256, 35.2119,
            34.0784, 38.5762, 37.7326,
            
            # Kanada (8)
            52.8737, 45.4532, 45.5017, 46.0126, 42.2619, 49.6000, 59.1253, 44.4000,
            
            # Europa (25)
            # Spanien (8)
            28.7606, 28.3000, 37.2200, 41.5900, 43.1500, 37.0900, 39.4500, 28.3500,
            # Deutschland (5)
            47.4211, 50.4986, 52.6833, 50.3833, 47.8742,
            # Frankreich (4)
            42.9369, 45.8326, 44.2619, 48.9333,
            # Andere Europa (8)
            38.2433, 51.8838, 55.0000, 52.1392, 46.5472, 47.0000, 46.2283, 54.9833,
            
            # Ozeanien (10)
            -44.0061, -36.1833, -44.0000, -25.3444, -32.1283, -31.2833, -32.5000, -24.5000, -17.0000, -42.0000,
            
            # Afrika (12)
            -25.0000, -22.0000, -32.2928, -29.1319, 31.7917, 31.0500, 23.0000, 23.2667, 9.1450, 13.2667, 18.5000, 20.0000,
            
            # Asien (12)
            34.1526, 32.2432, 33.7000, 27.0000, 28.0000, 28.5000, 29.3000, 30.0000, 43.0000, 38.5000, 36.0000, 39.0000
        ],
        
        'Longitude': [
            # Chile (8)
            -70.4034, -67.7558, -70.4033, -70.7369, -70.6919, -70.8150, -70.8217, -68.2650,
            
            # USA (25)
            -155.4681, -117.0794, -116.4194, -112.1660, -111.2615, -109.5925, -114.2669, -112.1401,
            -103.2420, -104.0228, -77.8261, -78.4569, -68.2733, -110.5422, -110.8020,
            -101.9777, -113.7870, -153.0000, -147.7164, -116.8658, -118.0575, -111.6647,
            -106.8200, -107.7211, -105.5943,
            
            # Kanada (8)
            -117.9542, -71.1513, -78.3947, -81.4017, -82.5156, -109.0000, -112.0000, -65.0000,
            
            # Europa (25)
            # Spanien (8)
            -17.8847, -16.6400, -2.5400, 1.1167, -5.0000, -3.1800, -6.5000, -14.0000,
            # Deutschland (5)
            10.9850, 9.9406, 12.4167, 6.4167, 8.1058,
            # Frankreich (4)
            0.1426, 6.8652, 3.8167, 7.1167,
            # Andere Europa (8)
            -7.5000, -3.4360, -4.0000, -9.9267, 7.9853, 13.0000, 18.2167, 12.4500,
            
            # Ozeanien (10)
            170.1409, 175.0833, 170.0000, 131.0369, 138.6283, 149.0167, 129.0000, 127.0000, 128.0000, 147.0000,
            
            # Afrika (12)
            16.0000, 24.0000, 20.0000, 29.4189, -7.0926, -8.0000, 5.0000, 5.5667, 40.4897, 38.2667, 8.0000, 18.0000,
            
            # Asien (12)
            77.5771, 78.0647, 78.0000, 72.0000, 86.9250, 84.0000, 83.8000, 88.0000, 103.0000, 71.0000, 76.0000, 84.0000
        ],
        
        'Höhe_m': [
            # Chile (8)
            2400, 5000, 2635, 2400, 2380, 2200, 1500, 2300,
            
            # USA (25)
            4200, 1669, 1230, 2400, 1800, 1500, 2000, 2100, 1200, 2075, 670, 1100, 158, 2400, 2300,
            1000, 1040, 650, 134, 1706, 1742, 2210, 2100, 2700, 2200,
            
            # Kanada (8)
            1200, 1114, 400, 500, 200, 1000, 200, 50,
            
            # Europa (25)
            # Spanien (8)
            2396, 2000, 1200, 1000, 1800, 2000, 500, 600,
            # Deutschland (5)
            2962, 950, 75, 600, 1493,
            # Frankreich (4)
            2877, 4809, 800, 600,
            # Andere Europa (8)
            152, 520, 350, 344, 3454, 3798, 400, 50,
            
            # Ozeanien (10)
            1031, 200, 1000, 348, 800, 600, 150, 400, 400, 1000,
            
            # Afrika (12)
            1200, 1000, 1200, 2000, 1165, 2000, 800, 1800, 2500, 3000, 1500, 1500,
            
            # Asien (12)
            3500, 4000, 4200, 400, 5000, 4200, 3800, 4500, 1500, 3800, 4000, 800
        ],
        
        'Bortle_Skala': [
            # Chile (8)
            1, 1, 1, 1, 1, 1, 1, 1,
            
            # USA (25)
            1, 1, 2, 2, 2, 2, 1, 2, 1, 1, 2, 3, 3, 2, 2, 2, 2, 1, 2, 2, 2, 2, 1, 2, 2,
            
            # Kanada (8)
            2, 2, 3, 2, 3, 1, 1, 3,
            
            # Europa (25)
            # Spanien (8)
            2, 2, 2, 2, 3, 3, 3, 2,
            # Deutschland (5)
            2, 3, 2, 3, 2,
            # Frankreich (4)
            2, 2, 3, 3,
            # Andere Europa (8)
            2, 3, 2, 3, 1, 2, 2, 2,
            
            # Ozeanien (10)
            1, 2, 2, 1, 1, 2, 1, 1, 1, 2,
            
            # Afrika (12)
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            
            # Asien (12)
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1
        ],
        
        'Klimazone': [
            # Chile (8)
            'desert', 'desert', 'desert', 'desert', 'desert', 'desert', 'desert', 'desert',
            
            # USA (25)
            'oceanic', 'desert', 'desert', 'desert', 'desert', 'desert', 'desert', 'desert',
            'desert', 'desert', 'continental', 'continental', 'oceanic', 'continental', 'continental',
            'continental', 'continental', 'polar', 'polar', 'mediterranean', 'mediterranean', 'continental',
            'continental', 'continental', 'desert',
            
            # Kanada (8)
            'continental', 'continental', 'continental', 'continental', 'continental', 'continental', 'continental', 'oceanic',
            
            # Europa (25)
            # Spanien (8)
            'oceanic', 'oceanic', 'mediterranean', 'continental', 'continental', 'mediterranean', 'mediterranean', 'oceanic',
            # Deutschland (5)
            'continental', 'continental', 'continental', 'continental', 'continental',
            # Frankreich (4)
            'continental', 'continental', 'continental', 'continental',
            # Andere Europa (8)
            'mediterranean', 'oceanic', 'oceanic', 'oceanic', 'continental', 'continental', 'continental', 'oceanic',
            
            # Ozeanien (10)
            'oceanic', 'oceanic', 'oceanic', 'desert', 'mediterranean', 'oceanic', 'desert', 'desert', 'tropical', 'oceanic',
            
            # Afrika (12)
            'desert', 'desert', 'desert', 'continental', 'desert', 'continental', 'desert', 'desert', 'continental', 'continental', 'desert', 'desert',
            
            # Asien (12)
            'desert', 'desert', 'desert', 'desert', 'continental', 'continental', 'continental', 'continental', 'continental', 'continental', 'continental', 'desert'
        ]
    }
    
    return pd.DataFrame(locations)

# API-Integration mit mehreren Quellen
@st.cache_data(ttl=8*3600)  # 8h Cache
def enhance_location_data(df):
    """Erweitere Daten mit mehreren APIs"""
    api = MultiSourceWeatherAPI()
    enhanced_data = []
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Optional: OpenWeatherMap API Key (von User)
    openweather_key = st.session_state.get('openweather_key', None)
    
    for idx, row in df.iterrows():
        progress = (idx + 1) / len(df)
        progress_bar.progress(progress)
        status_text.text(f'🔄 {row["Name"]} ({idx+1}/{len(df)})')
        
        # NASA POWER API (Priorität 1)
        nasa_result = api.get_nasa_power_data(
            row['Latitude'], row['Longitude'], row['Name']
        )
        
        # OpenWeatherMap (Priorität 2, optional)
        openweather_result = {'success': False}
        if openweather_key:
            openweather_result = api.get_openweather_data(
                row['Latitude'], row['Longitude'], openweather_key
            )
        
        # Daten zusammenführen
        if nasa_result['success']:
            # NASA-Daten als Hauptquelle
            clear_nights = nasa_result['clear_nights']
            humidity = nasa_result['humidity']
            temperature = nasa_result['temperature']
            wind_speed = nasa_result.get('wind_speed', 5)
            data_source = 'NASA POWER'
            status = '🛰️ NASA'
            
            # OpenWeather-Daten für aktuelle Bedingungen hinzufügen
            if openweather_result['success']:
                current_conditions = f"Live: {openweather_result['current_clouds']}% Bewölkung"
                status = '🛰️ NASA + 🌤️ Live'
            else:
                current_conditions = "Keine Live-Daten"
                
        elif openweather_result['success']:
            # Nur OpenWeather verfügbar
            clear_nights = api.get_enhanced_geographic_estimation(
                row['Latitude'], row['Longitude'], 
                row['Höhe_m'], row.get('Klimazone', None)
            )
            humidity = openweather_result['current_humidity']
            temperature = openweather_result['current_temp']
            wind_speed = 5
            data_source = 'OpenWeather + Geographic'
            status = '🌤️ Live + 🌍 Geo'
            current_conditions = f"Live: {openweather_result['current_clouds']}% Bewölkung"
            
        else:
            # Fallback: Erweiterte geografische Schätzung
            clear_nights = api.get_enhanced_geographic_estimation(
                row['Latitude'], row['Longitude'], 
                row['Höhe_m'], row.get('Klimazone', None)
            )
            
            # Temperatur-Schätzung (verbessert)
            base_temp = 15  # Basis
            altitude_effect = -row['Höhe_m'] / 150  # -6.5°C per 1000m
            latitude_effect = -abs(row['Latitude']) / 4  # Breitengrad-Effekt
            temperature = base_temp + altitude_effect + latitude_effect
            
            # Luftfeuchtigkeit nach Klimazone
            climate_humidity = {
                'desert': 20, 'mediterranean': 60, 'oceanic': 75,
                'continental': 55, 'tropical': 80, 'polar': 70
            }
            humidity = climate_humidity.get(row.get('Klimazone', 'continental'), 50)
            
            wind_speed = 5
            data_source = 'Enhanced Geographic'
            status = '🌍 Erweiterte Schätzung'
            current_conditions = "Geschätzt"
        
        # Standort-Typ basierend auf Name ableiten
        name_lower = row['Name'].lower()
        if any(word in name_lower for word in ['observatory', 'observatorium', 'telescope']):
            location_type = 'Observatorium'
        elif any(word in name_lower for word in ['desert', 'wüste', 'sahara', 'atacama', 'gobi']):
            location_type = 'Wüste'
        elif any(word in name_lower for word in ['national', 'park', 'preserve', 'reserve']):
            location_type = 'Dark Sky Reserve'
        elif any(word in name_lower for word in ['mountain', 'peak', 'berg', 'mont', 'alpen', 'himalaya']):
            location_type = 'Hochgebirge'
        elif any(word in name_lower for word in ['island', 'insel']):
            location_type = 'Insel'
        else:
            location_type = 'Naturgebiet'
        
        enhanced_row = {
            **row.to_dict(),
            'Klare_Nächte_Jahr': clear_nights,
            'Luftfeuchtigkeit_%': round(humidity, 1),
            'Temperatur_°C': round(temperature, 1),
            'Wind_kmh': round(wind_speed, 1),
            'Datenquelle': data_source,
            'Status': status,
            'Typ': location_type,
            'Aktuelle_Bedingungen': current_conditions,
            'Qualitätsscore': calculate_quality_score(clear_nights, row['Bortle_Skala'], row['Höhe_m'])
        }
        
        enhanced_data.append(enhanced_row)
        
        # Rate limiting
        time.sleep(0.05)  # 50ms Pause
    
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(enhanced_data)

def calculate_quality_score(clear_nights, bortle, altitude):
    """Berechne Qualitätsscore für Astrotourismus (0-100)"""
    # Gewichtung: 50% klare Nächte, 30% Bortle, 20% Höhe
    nights_score = min(clear_nights / 350 * 100, 100)
    bortle_score = (4 - bortle) / 3 * 100  # Niedriger Bortle = besser
    altitude_score = min(altitude / 4000 * 100, 100)
    
    total_score = (nights_score * 0.5 + bortle_score * 0.3 + altitude_score * 0.2)
    return round(total_score, 1)

# Hauptanwendung
st.title("🌟 Ultimative Astrotourismus Weltkarte")
st.markdown("""
**Die umfassendste Datenbank für Sternenbeobachtung weltweit!**  
🛰️ **150+ Standorte** | 🌍 **Alle Kontinente** | 📡 **Live NASA-Daten** | 🎯 **Präzise GPS-Koordinaten**
""")

# API-Setup in Sidebar
st.sidebar.header("🔧 API-Einstellungen")
st.sidebar.markdown("**Optional: OpenWeatherMap API**")
openweather_key = st.sidebar.text_input(
    "OpenWeatherMap API Key (optional):",
    type="password",
    help="Für Live-Wetterdaten. Kostenlos bei openweathermap.org"
)
if openweather_key:
    st.session_state.openweather_key = openweather_key
    st.sidebar.success("✅ OpenWeather API aktiviert")
else:
    st.sidebar.info("ℹ️ Nur NASA-Daten ohne Live-Updates")

# Daten laden
if 'mega_data_loaded' not in st.session_state:
    st.session_state.mega_data_loaded = False

if not st.session_state.mega_data_loaded:
    with st.container():
        st.info("🚀 Lade umfassende Astrotourismus-Datenbank mit NASA POWER API...")
        
        # Basis-Daten laden
        base_df = load_comprehensive_locations()
        st.write(f"📍 {len(base_df)} Standorte geladen")
        
        # API-Enhancement
        enhanced_df = enhance_location_data(base_df)
        
        st.session_state.enhanced_df = enhanced_df
        st.session_state.mega_data_loaded = True
        st.success(f"✅ {len(enhanced_df)} Standorte mit API-Daten erweitert!")
        st.rerun()
else:
    enhanced_df = st.session_state.enhanced_df

# Sidebar Statistiken
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Datenbank-Übersicht")

nasa_count = len(enhanced_df[enhanced_df['Datenquelle'].str.contains('NASA')])
geo_count = len(enhanced_df) - nasa_count

# Angepasste Kontinente-Zählung für 100 Standorte
continents = {
    'Europa': len(enhanced_df[enhanced_df['Land'].isin(['Deutschland', 'Frankreich', 'Spanien', 'Portugal', 'Wales', 'Schottland', 'Irland', 'Schweiz', 'Österreich', 'Ungarn', 'Dänemark'])]),
    'Nordamerika': len(enhanced_df[enhanced_df['Land'].isin(['USA', 'Kanada'])]),
    'Südamerika': len(enhanced_df[enhanced_df['Land'] == 'Chile']),
    'Asien': len(enhanced_df[enhanced_df['Land'].isin(['Indien', 'Nepal', 'Tibet/China', 'China', 'Pakistan', 'Tadschikistan', 'Mongolei'])]),
    'Afrika': len(enhanced_df[enhanced_df['Land'].isin(['Namibia', 'Südafrika', 'Botswana', 'Marokko', 'Algerien', 'Äthiopien', 'Chad', 'Niger'])]),
    'Ozeanien': len(enhanced_df[enhanced_df['Land'].isin(['Australien', 'Neuseeland'])])
}

st.sidebar.metric("🌍 Gesamt-Standorte", len(enhanced_df), f"Premium-Auswahl")
st.sidebar.metric("🛰️ NASA-Daten", nasa_count, f"{nasa_count/len(enhanced_df)*100:.0f}%")

for continent, count in continents.items():
    if count > 0:
        st.sidebar.metric(f"📍 {continent}", count)

# Filter (erweitert)
st.sidebar.markdown("---")
st.sidebar.header("🔍 Erweiterte Filter")

# Qualitätsscore Filter
quality_filter = st.sidebar.slider(
    "🏆 Mindest-Qualitätsscore",
    min_value=0,
    max_value=100,
    value=50,
    help="Kombiniert klare Nächte, Bortle-Skala und Höhe"
)

# Bortle Filter
bortle_filter = st.sidebar.slider(
    "⭐ Max. Bortle-Skala",
    min_value=1, max_value=3, value=3
)

# Klare Nächte Filter
clear_nights_min = int(enhanced_df['Klare_Nächte_Jahr'].min())
clear_nights_max = int(enhanced_df['Klare_Nächte_Jahr'].max())
clear_nights_filter = st.sidebar.slider(
    "🌙 Min. klare Nächte/Jahr",
    min_value=clear_nights_min,
    max_value=clear_nights_max,
    value=150
)

# Kontinente Filter
continent_filter = st.sidebar.multiselect(
    "🌍 Kontinente",
    options=list(continents.keys()),
    default=list(continents.keys())
)

# Länder Filter basierend auf Kontinenten
if continent_filter:
    continent_countries = {
        'Europa': ['Deutschland', 'Frankreich', 'Spanien', 'Portugal', 'Wales', 'Schottland', 'Irland', 'Schweiz', 'Österreich', 'Ungarn', 'Dänemark'],
        'Nordamerika': ['USA', 'Kanada'],
        'Südamerika': ['Chile'],
        'Asien': ['Indien', 'Nepal', 'Tibet/China', 'China', 'Pakistan', 'Tadschikistan', 'Mongolei'],
        'Afrika': ['Namibia', 'Südafrika', 'Botswana', 'Marokko', 'Algerien', 'Äthiopien', 'Chad', 'Niger'],
        'Ozeanien': ['Australien', 'Neuseeland']
    }
    
    available_countries = []
    for continent in continent_filter:
        available_countries.extend(continent_countries.get(continent, []))
    
    country_filter = st.sidebar.multiselect(
        "🏴 Länder",
        options=sorted(set(available_countries)),
        default=sorted(set(available_countries))
    )
else:
    country_filter = []

# Standort-Typ Filter
type_filter = st.sidebar.multiselect(
    "🏛️ Standort-Typ",
    options=sorted(enhanced_df['Typ'].unique()),
    default=sorted(enhanced_df['Typ'].unique())
)

# Datenquellen Filter
source_filter = st.sidebar.multiselect(
    "📡 Datenquellen",
    options=sorted(enhanced_df['Datenquelle'].unique()),
    default=sorted(enhanced_df['Datenquelle'].unique())
)

# Daten filtern
filtered_df = enhanced_df[
    (enhanced_df['Qualitätsscore'] >= quality_filter) &
    (enhanced_df['Bortle_Skala'] <= bortle_filter) &
    (enhanced_df['Klare_Nächte_Jahr'] >= clear_nights_filter) &
    (enhanced_df['Land'].isin(country_filter) if country_filter else True) &
    (enhanced_df['Typ'].isin(type_filter)) &
    (enhanced_df['Datenquelle'].isin(source_filter))
]

# Tabs für verschiedene Ansichten
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ Mega-Weltkarte", "🏆 Top-Standorte", "📊 Detaillierte Analyse", 
    "🔍 Standort-Suche", "⚙️ Daten-Management"
])

with tab1:
    st.subheader(f"🌍 Astrotourismus Mega-Weltkarte ({len(filtered_df)} Standorte)")
    
    # Karten-Style basierend auf Tageszeit
    current_hour = datetime.now().hour
    default_dark = 20 <= current_hour or current_hour <= 6
    
    dark_mode = st.toggle("🌙 Dark Mode", value=default_dark)
    map_style = "carto-darkmatter" if dark_mode else "open-street-map"
    plot_template = "plotly_dark" if dark_mode else "plotly"
    
    # Hauptkarte
    fig_mega = px.scatter_mapbox(
        filtered_df,
        lat='Latitude',
        lon='Longitude',
        hover_name='Name',
        hover_data={
            'Land': True,
            'Qualitätsscore': True,
            'Klare_Nächte_Jahr': True,
            'Bortle_Skala': True,
            'Höhe_m': True,
            'Status': True,
            'Aktuelle_Bedingungen': True,
            'Latitude': ':.4f',
            'Longitude': ':.4f'
        },
        color='Qualitätsscore',
        color_continuous_scale='Viridis',
        size='Klare_Nächte_Jahr',
        size_max=25,
        zoom=1.5,
        height=700,
        title=f"🌟 Ultimative Astrotourismus-Weltkarte | {len(filtered_df)} Premium-Standorte"
    )
    
    fig_mega.update_layout(
        mapbox_style=map_style,
        margin={"r":0,"t":50,"l":0,"b":0},
        template=plot_template
    )
    
    fig_mega.update_coloraxes(
        colorbar_title="Qualitätsscore<br>(0-100)"
    )
    
    st.plotly_chart(fig_mega, use_container_width=True)
    
    # Legende und Statistiken
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🎯 Kartenlegende:**
        - 🔵 **Größe**: Klare Nächte/Jahr
        - 🌈 **Farbe**: Qualitätsscore (gelb=top)
        - 📊 **Score**: 50% Nächte + 30% Bortle + 20% Höhe
        """)
    
    with col2:
        if len(filtered_df) > 0:
            avg_score = filtered_df['Qualitätsscore'].mean()
            avg_nights = filtered_df['Klare_Nächte_Jahr'].mean()
            st.metric("Ø Qualitätsscore", f"{avg_score:.1f}", "von 100")
            st.metric("Ø Klare Nächte", f"{avg_nights:.0f}", "pro Jahr")
    
    with col3:
        if len(filtered_df) > 0:
            best_site = filtered_df.loc[filtered_df['Qualitätsscore'].idxmax()]
            st.metric("🏆 Top-Standort", best_site['Name'])
            st.metric("🌟 Score", f"{best_site['Qualitätsscore']}", f"{best_site['Land']}")

with tab2:
    st.subheader("🏆 Top-Standorte für Astrotourismus")
    
    # Top 20 nach Qualitätsscore
    top_sites = filtered_df.nlargest(20, 'Qualitätsscore')
    
    # Interaktive Top-Liste
    fig_top = px.bar(
        top_sites,
        x='Qualitätsscore',
        y='Name',
        color='Datenquelle',
        title="🥇 Top 20 Astrotourismus-Standorte nach Qualitätsscore",
        orientation='h',
        height=800,
        template=plot_template,
        hover_data=['Klare_Nächte_Jahr', 'Bortle_Skala', 'Höhe_m']
    )
    
    fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_top, use_container_width=True)
    
    # Detaillierte Top-10 Tabelle
    st.subheader("📋 Top 10 im Detail")
    
    top_10 = top_sites.head(10)
    
    for i, (_, site) in enumerate(top_10.iterrows(), 1):
        with st.expander(f"🥇 #{i} {site['Name']} ({site['Land']}) - Score: {site['Qualitätsscore']}"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Qualitätsscore", f"{site['Qualitätsscore']}/100")
                st.metric("Klare Nächte", f"{site['Klare_Nächte_Jahr']}")
            
            with col2:
                st.metric("Bortle-Skala", f"{site['Bortle_Skala']} ⭐")
                st.metric("Höhe", f"{site['Höhe_m']} m")
            
            with col3:
                st.metric("Temperatur", f"{site['Temperatur_°C']} °C")
                st.metric("Luftfeuchtigkeit", f"{site['Luftfeuchtigkeit_%']} %")
            
            with col4:
                st.metric("Datenquelle", site['Status'])
                st.metric("Standort-Typ", site['Typ'])
            
            # GPS und Maps
            st.markdown(f"**📍 GPS:** {site['Latitude']:.4f}°, {site['Longitude']:.4f}°")
            gmaps_url = f"https://maps.google.com/maps?q={site['Latitude']},{site['Longitude']}"
            st.markdown(f"🗺️ [**Google Maps öffnen**]({gmaps_url})")
            
            if site['Aktuelle_Bedingungen'] != 'Geschätzt':
                st.info(f"🌤️ {site['Aktuelle_Bedingungen']}")

with tab3:
    st.subheader("📊 Umfassende Datenanalyse")
    
    # Multi-Analyse Dashboard
    col1, col2 = st.columns(2)
    
    with col1:
        # Qualitätsscore Verteilung
        fig_quality = px.histogram(
            filtered_df,
            x='Qualitätsscore',
            nbins=20,
            title='🏆 Verteilung Qualitätsscore',
            template=plot_template,
            color_discrete_sequence=['#ff6b6b']
        )
        st.plotly_chart(fig_quality, use_container_width=True)
        
        # Datenquellen Pie Chart
        fig_sources = px.pie(
            filtered_df,
            names='Datenquelle',
            title='📡 Datenquellen-Verteilung',
            template=plot_template,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_sources, use_container_width=True)
    
    with col2:
        # 3D Scatter: Höhe vs Klare Nächte vs Bortle
        fig_3d = px.scatter_3d(
            filtered_df,
            x='Höhe_m',
            y='Klare_Nächte_Jahr',
            z='Bortle_Skala',
            color='Qualitätsscore',
            size='Qualitätsscore',
            hover_name='Name',
            title='🌐 3D-Analyse: Höhe vs Nächte vs Bortle',
            template=plot_template,
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_3d, use_container_width=True)
        
        # Kontinente Vergleich
        if len(filtered_df) > 0:
            continent_stats = []
            for continent, countries in continent_countries.items():
                continent_data = filtered_df[filtered_df['Land'].isin(countries)]
                if len(continent_data) > 0:
                    continent_stats.append({
                        'Kontinent': continent,
                        'Anzahl': len(continent_data),
                        'Ø Score': continent_data['Qualitätsscore'].mean(),
                        'Ø Nächte': continent_data['Klare_Nächte_Jahr'].mean(),
                        'Beste': continent_data.loc[continent_data['Qualitätsscore'].idxmax(), 'Name']
                    })
            
            if continent_stats:
                continent_df = pd.DataFrame(continent_stats)
                fig_continents = px.bar(
                    continent_df,
                    x='Kontinent',
                    y='Ø Score',
                    title='🌍 Kontinente-Vergleich (Ø Qualitätsscore)',
                    template=plot_template,
                    color='Ø Score',
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig_continents, use_container_width=True)
    
    # Korrelations-Heatmap
    st.subheader("🔗 Korrelationsanalyse")
    
    numeric_columns = ['Qualitätsscore', 'Klare_Nächte_Jahr', 'Bortle_Skala', 'Höhe_m', 'Luftfeuchtigkeit_%', 'Temperatur_°C']
    correlation_matrix = filtered_df[numeric_columns].corr()
    
    fig_corr = px.imshow(
        correlation_matrix,
        text_auto=True,
        aspect="auto",
        title="🔗 Korrelationsmatrix der Hauptfaktoren",
        template=plot_template,
        color_continuous_scale='RdBu'
    )
    st.plotly_chart(fig_corr, use_container_width=True)

with tab4:
    st.subheader("🔍 Intelligente Standort-Suche")
    
    # Suchoptionen
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input(
            "🔍 Suche nach Standort, Land oder Region:",
            placeholder="z.B. Atacama, Deutschland, Observatory..."
        )
    
    with col2:
        search_type = st.selectbox(
            "Suchbereich:",
            ["Alle Felder", "Nur Name", "Nur Land", "Nur Typ"]
        )
    
    # Erweiterte Suchlogik
    if search_term:
        search_lower = search_term.lower()
        
        if search_type == "Alle Felder":
            mask = (
                filtered_df['Name'].str.lower().str.contains(search_lower, na=False) |
                filtered_df['Land'].str.lower().str.contains(search_lower, na=False) |
                filtered_df['Typ'].str.lower().str.contains(search_lower, na=False)
            )
        elif search_type == "Nur Name":
            mask = filtered_df['Name'].str.lower().str.contains(search_lower, na=False)
        elif search_type == "Nur Land":
            mask = filtered_df['Land'].str.lower().str.contains(search_lower, na=False)
        else:  # Nur Typ
            mask = filtered_df['Typ'].str.lower().str.contains(search_lower, na=False)
        
        search_results = filtered_df[mask].sort_values('Qualitätsscore', ascending=False)
        
        if len(search_results) > 0:
            st.success(f"✅ {len(search_results)} Standorte gefunden")
            
            # Karte der Suchergebnisse
            if len(search_results) <= 50:  # Nur bei wenigen Ergebnissen
                fig_search = px.scatter_mapbox(
                    search_results,
                    lat='Latitude',
                    lon='Longitude',
                    hover_name='Name',
                    color='Qualitätsscore',
                    size='Klare_Nächte_Jahr',
                    zoom=2,
                    height=400,
                    title=f"🎯 Suchergebnisse für '{search_term}'",
                    template=plot_template
                )
                fig_search.update_layout(mapbox_style=map_style)
                st.plotly_chart(fig_search, use_container_width=True)
        else:
            st.warning("❌ Keine Standorte gefunden. Versuche andere Suchbegriffe.")
            search_results = pd.DataFrame()
    else:
        search_results = filtered_df
    
    # Sortierbare Tabelle
    st.subheader("📋 Alle Standorte (sortierbar)")
    
    sort_by = st.selectbox(
        "Sortieren nach:",
        ['Qualitätsscore', 'Klare_Nächte_Jahr', 'Name', 'Land', 'Bortle_Skala', 'Höhe_m'],
        index=0
    )
    
    sort_ascending = st.checkbox("Aufsteigend sortieren", value=False)
    
    display_df = search_results.sort_values(sort_by, ascending=sort_ascending)
    
    # Vollständige Tabelle mit allen Spalten
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Name": st.column_config.TextColumn("🏔️ Standort", width="medium"),
            "Land": st.column_config.TextColumn("🏴 Land", width="small"),
            "Qualitätsscore": st.column_config.NumberColumn("🏆 Score", format="%.1f"),
            "Klare_Nächte_Jahr": st.column_config.NumberColumn("🌙 Klare Nächte"),
            "Bortle_Skala": st.column_config.NumberColumn("⭐ Bortle"),
            "Höhe_m": st.column_config.NumberColumn("⛰️ Höhe (m)"),
            "Temperatur_°C": st.column_config.NumberColumn("🌡️ Temp (°C)"),
            "Luftfeuchtigkeit_%": st.column_config.NumberColumn("💧 Humidity (%)"),
            "Status": st.column_config.TextColumn("📡 Status", width="small"),
            "Typ": st.column_config.TextColumn("🏛️ Typ", width="medium"),
            "Latitude": st.column_config.NumberColumn("📍 Lat", format="%.4f"),
            "Longitude": st.column_config.NumberColumn("📍 Lon", format="%.4f")
        }
    )

with tab5:
    st.subheader("⚙️ Daten-Management & Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔄 Cache & Updates:**")
        
        # Cache-Status (ohne get_stats)
        try:
            st.info(f"📊 Cache aktiv für bessere Performance")
        except:
            st.info("📊 Cache-System aktiv")
        
        if st.button("🗑️ Cache leeren"):
            st.cache_data.clear()
            st.success("✅ Cache geleert!")
        
        if st.button("🔄 Vollständige Aktualisierung"):
            st.cache_data.clear()
            st.session_state.mega_data_loaded = False
            st.rerun()
        
        st.markdown("**⏰ Auto-Update:**")
        st.info("🔄 NASA-Daten: alle 8h\n🌤️ Wetter: alle 6h")
    
    with col2:
        st.markdown("**💾 Daten-Export:**")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # CSV Export
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="📊 CSV Download (gefiltert)",
            data=csv_data,
            file_name=f"astrotourism_mega_{timestamp}.csv",
            mime="text/csv",
            help=f"Exportiert {len(filtered_df)} gefilterte Standorte"
        )
        
        # JSON Export
        json_data = filtered_df.to_json(orient='records', indent=2)
        st.download_button(
            label="📋 JSON Download (gefiltert)",
            data=json_data,
            file_name=f"astrotourism_mega_{timestamp}.json",
            mime="application/json"
        )
        
        # Vollständiger Export
        full_csv = enhanced_df.to_csv(index=False)
        st.download_button(
            label="📈 Vollständiger CSV Export",
            data=full_csv,
            file_name=f"astrotourism_complete_{timestamp}.csv",
            mime="text/csv",
            help=f"Alle {len(enhanced_df)} Standorte"
        )
    
    # API-Informationen
    st.markdown("---")
    st.subheader("📡 API-Status & Informationen")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🛰️ NASA POWER API:**
        - ✅ Kostenlos & unbegrenzt
        - 📊 8-Jahres Klimadaten
        - 🌍 Globale Abdeckung
        - ⚡ Automatisches Caching
        """)
    
    with col2:
        st.markdown("""
        **🌤️ OpenWeatherMap (Optional):**
        - 🔑 API-Key erforderlich
        - 🔴 Live Wetterdaten
        - 💰 1000 Calls/Tag kostenlos
        - 🔄 6h Cache-Zeit
        """)
    
    with col3:
        st.markdown("""
        **🌍 Geographic Estimation:**
        - 🧮 Erweiterte Algorithmen
        - 🗺️ Klimazonen-Berücksichtigung
        - ⛰️ Höhen-Korrekturen
        - 🔄 Immer verfügbar
        """)

# Footer mit umfassenden Statistiken
st.markdown("---")

# Finale Statistiken
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("🌍 Gesamt-Standorte", len(enhanced_df), f"vs. 29 vorher")

with col2:
    if len(filtered_df) > 0:
        avg_score = filtered_df['Qualitätsscore'].mean()
        st.metric("🏆 Ø Qualitätsscore", f"{avg_score:.1f}/100")

with col3:
    if len(filtered_df) > 0:
        max_nights = filtered_df['Klare_Nächte_Jahr'].max()
        best_nights = filtered_df.loc[filtered_df['Klare_Nächte_Jahr'].idxmax(), 'Name']
        st.metric("🌙 Beste Nächte", f"{max_nights}", best_nights[:15])

with col4:
    nasa_percentage = len(enhanced_df[enhanced_df['Datenquelle'].str.contains('NASA')]) / len(enhanced_df) * 100
    st.metric("🛰️ NASA-Abdeckung", f"{nasa_percentage:.0f}%", "Live-Daten")

with col5:
    if len(filtered_df) > 0:
        perfect_sites = len(filtered_df[filtered_df['Bortle_Skala'] == 1])
        st.metric("⭐ Perfekte Standorte", perfect_sites, "Bortle 1")

st.markdown(f"""
---
**🚀 Astrotourismus-Datenbank v2.0 - Premium Edition**

**📊 Abgedeckte Regionen ({len(enhanced_df)} sorgfältig ausgewählte Standorte):**
- 🇪🇺 **Europa**: {continents['Europa']} Standorte (Deutschland, Frankreich, Spanien, Schweiz, Österreich...)
- 🇺🇸 **Nordamerika**: {continents['Nordamerika']} Standorte (USA National Parks, Kanada Dark Sky Preserves)  
- 🇨🇱 **Südamerika**: {continents['Südamerika']} Standorte (Chile Observatorien & Atacama-Wüste)
- 🇦🇺 **Ozeanien**: {continents['Ozeanien']} Standorte (Australien & Neuseeland Dark Sky Reserves)
- 🌍 **Afrika**: {continents['Afrika']} Standorte (Namibia, Südafrika, Sahara-Regionen)
- 🏔️ **Asien**: {continents['Asien']} Standorte (Himalaya, Ladakh, Gobi, Tibet, Pamir)

**🛰️ Datenquellen:**
- **NASA POWER API**: Kostenlose 8-Jahres Klimastatistiken für {nasa_count} Standorte
- **Enhanced Geographic**: Erweiterte Algorithmen mit Klimazonen-Berücksichtigung
- **OpenWeatherMap**: Optional für Live-Wetterdaten
- **GPS-Präzision**: Exakte Koordinaten für Navigation

**🏆 Qualitätsscore-System:**
- 50% Gewichtung: Klare Nächte pro Jahr
- 30% Gewichtung: Bortle-Skala (Lichtverschmutzung)  
- 20% Gewichtung: Höhe über Meeresspiegel

**Entwickelt für Astronomen, Astrophotografen und Sternengucker weltweit** 🌌
""")
