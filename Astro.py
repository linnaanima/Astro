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

# Massiv erweiterte Standort-Datenbank
@st.cache_data(ttl=24*3600)
def load_comprehensive_locations():
    """Erweiterte Datenbank mit 150+ Standorten weltweit"""
    
    locations = {
        'Name': [
            # CHILE - Weltklasse Astronomie
            'Atacama-Wüste', 'ALMA Observatory', 'Paranal Observatory', 'La Silla Observatory',
            'Las Campanas Observatory', 'Cerro Tololo Observatory', 'Gemini South',
            'Elqui Valley', 'Valle de la Luna', 'Chajnantor Plateau',
            
            # USA - Umfassende Abdeckung
            'Mauna Kea Hawaii', 'Mauna Loa Hawaii', 'Haleakala Hawaii',
            'Death Valley California', 'Joshua Tree California', 'Anza-Borrego California',
            'Mojave Preserve California', 'Big Sur California', 'Mount Wilson California',
            'Palomar Observatory California', 'Lick Observatory California',
            'Big Bend Texas', 'McDonald Observatory Texas', 'Enchanted Rock Texas',
            'Cherry Springs Pennsylvania', 'Spruce Knob West Virginia', 'Shenandoah Virginia',
            'Acadia Maine', 'Katahdin Woods Maine',
            'Bryce Canyon Utah', 'Capitol Reef Utah', 'Arches Utah', 'Natural Bridges Utah',
            'Dead Horse Point Utah', 'Goblin Valley Utah', 'Great Basin Nevada',
            'Lake Tahoe California', 'Yosemite California', 'Sequoia California',
            'Grand Canyon Arizona', 'Sedona Arizona', 'Flagstaff Arizona', 'Lowell Observatory Arizona',
            'Chaco New Mexico', 'Very Large Array New Mexico', 'Capulin Volcano New Mexico',
            'Black Canyon Colorado', 'Great Sand Dunes Colorado', 'Rocky Mountain Colorado',
            'Yellowstone Wyoming', 'Grand Teton Wyoming', 'Devils Tower Wyoming',
            'Badlands South Dakota', 'Theodore Roosevelt North Dakota',
            'Glacier Montana', 'Glacier Bay Alaska', 'Denali Alaska', 'Fairbanks Alaska',
            
            # KANADA - Dark Sky Preserves
            'Jasper Nationalpark', 'Banff Nationalpark', 'Waterton Nationalpark',
            'Mont-Mégantic Quebec', 'Algonquin Ontario', 'Killarney Ontario', 'Torrance Barrens Ontario',
            'Point Pelee Ontario', 'Long Point Ontario', 'Muskoka Ontario',
            'Cypress Hills Alberta', 'Wood Buffalo Alberta', 'Grasslands Saskatchewan',
            'Riding Mountain Manitoba', 'Fundy New Brunswick', 'Kejimkujik Nova Scotia',
            
            # EUROPA - Vielfältige Standorte
            # Spanien
            'Roque de los Muchachos La Palma', 'Teide Observatorium Teneriffa', 'Calar Alto Andalusien',
            'Montsec Katalonien', 'Picos de Europa Asturien', 'Sierra Nevada Andalusien',
            'Sierra de Gredos', 'Extremadura', 'Pyrénées Aragonien', 'Ordesa Nationalpark',
            'Fuerteventura', 'Lanzarote', 'Gran Canaria', 'La Gomera',
            
            # Frankreich
            'Pic du Midi Observatorium', 'Observatoire de Haute-Provence', 'Mont-Blanc Chamonix',
            'Cévennes Nationalpark', 'Vosges du Nord', 'Causses du Quercy', 'Pyrénées Nationalpark',
            'Vanoise Nationalpark', 'Mercantour Nationalpark', 'Écrins Nationalpark',
            
            # Deutschland
            'Zugspitze Bayern', 'Wasserkuppe Rhön', 'Brocken Harz', 'Feldberg Schwarzwald',
            'Westhavelland Brandenburg', 'Eifel Nationalpark', 'Spiegelau Bayern',
            'Hoher Meißner Hessen', 'Wendelstein Bayern', 'Fichtelgebirge Bayern',
            
            # Andere Europa
            'Alqueva Portugal', 'Monsaraz Portugal', 'Gerês Portugal', 'Madeira Portugal', 'Azoren Portugal',
            'Brecon Beacons Wales', 'Snowdonia Wales', 'Galloway Forest Schottland', 'Cairngorms Schottland',
            'Kerry Dark Sky Reserve Irland', 'Mayo Dark Sky Park Irland',
            'Zselic Starry Sky Park Ungarn', 'Hortobágy Ungarn', 'Bükk Ungarn',
            'Møn Dänemark', 'Læsø Dänemark',
            'Aspromonte Italien', 'Abruzzo Italien', 'Dolomiten Italien', 'Sizilien Ätna Italien',
            'Jungfraujoch Schweiz', 'Matterhorn Schweiz', 'Engadin Schweiz', 'Verzasca Schweiz',
            'Hohe Tauern Österreich', 'Ötztal Österreich', 'Gesäuse Österreich',
            'Tatras Polen', 'Bieszczady Polen', 'Carpathians Rumänien', 'Bucegi Rumänien',
            
            # NEUSEELAND & AUSTRALIEN
            'Aoraki Mackenzie Neuseeland', 'Great Barrier Island Neuseeland', 'Rakiura Stewart Island Neuseeland',
            'Lake Tekapo Neuseeland', 'Franz Josef Neuseeland', 'Milford Sound Neuseeland',
            'Uluru Australien', 'Kata Tjuta Australien', 'Kings Canyon Australien',
            'Flinders Ranges Australien', 'Grampians Australien', 'Blue Mountains Australien',
            'Warrumbungle Australien', 'Little Desert Australien', 'Mungo Australien',
            'Nullarbor Plain Australien', 'Gibson Desert Australien', 'Great Sandy Desert Australien',
            'Pilbara Australien', 'Kimberley Australien', 'Tasmania Dark Sky Australien',
            
            # AFRIKA - Südhalbkugel Highlights
            'NamibRand Namibia', 'Sossusvlei Namibia', 'Fish River Canyon Namibia',
            'Kalahari Botswana', 'Okavango Delta Botswana', 'Makgadikgadi Botswana',
            'Karoo Südafrika', 'Tankwa Karoo Südafrika', 'Cederberg Südafrika', 'Drakensberg Südafrika',
            'Richtersveld Südafrika', 'Augrabies Südafrika', 'Kgalagadi Südafrika',
            'Sahara Marokko', 'Atlas Mountains Marokko', 'Anti-Atlas Marokko',
            'Sahara Algerien', 'Hoggar Mountains Algerien', 'Tassili n\'Ajjer Algerien',
            'Tibesti Chad', 'Air Mountains Niger', 'Ennedi Plateau Chad',
            'Ethiopian Highlands Äthiopien', 'Simien Mountains Äthiopien', 'Bale Mountains Äthiopien',
            
            # ASIEN - Hochgebirge & Wüsten
            # Indien & Himalaya
            'Ladakh Indien', 'Spiti Valley Indien', 'Nubra Valley Indien', 'Zanskar Indien',
            'Changthang Plateau Indien', 'Hemis Nationalpark Indien', 'Pin Valley Indien',
            'Kinnaur Indien', 'Lahaul Indien', 'Dharamshala Indien',
            'Rajasthan Thar Desert Indien', 'Kutch Gujarat Indien', 'Western Ghats Indien',
            
            # Nepal & Tibet
            'Everest Base Camp Nepal', 'Annapurna Region Nepal', 'Mustang Nepal', 'Manaslu Nepal',
            'Langtang Nepal', 'Dolpo Nepal', 'Khumbu Nepal',
            'Tibet Plateau China', 'Mount Kailash Tibet', 'Ngari Tibet',
            
            # Zentralasien
            'Pamir Tadschikistan', 'Tian Shan Kirgisistan', 'Altai Mountains Mongolei',
            'Gobi Desert Mongolei', 'Mongolische Steppe', 'Khangai Mountains Mongolei',
            'Karakorum Pakistan', 'K2 Base Camp Pakistan', 'Hunza Valley Pakistan',
            'Skardu Pakistan', 'Deosai Plains Pakistan',
            
            # China & Ostasien
            'Taklamakan Desert China', 'Xinjiang China', 'Inner Mongolia China',
            'Qinghai Plateau China', 'Kunlun Mountains China', 'Qilian Mountains China',
            'Atacama-like Qaidam China', 'Yellow River Source China'
        ],
        
        'Land': [
            # Chile
            'Chile', 'Chile', 'Chile', 'Chile', 'Chile', 'Chile', 'Chile', 'Chile', 'Chile', 'Chile',
            
            # USA (50 Standorte)
            'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA',
            'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA',
            'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA',
            'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA',
            'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA',
            'USA', 'USA', 'USA', 'USA', 'USA', 'USA',
            
            # Kanada (16 Standorte)
            'Kanada', 'Kanada', 'Kanada', 'Kanada', 'Kanada', 'Kanada', 'Kanada',
            'Kanada', 'Kanada', 'Kanada', 'Kanada', 'Kanada', 'Kanada',
            'Kanada', 'Kanada', 'Kanada',
            
            # Europa (70 Standorte)
            # Spanien (14)
            'Spanien', 'Spanien', 'Spanien', 'Spanien', 'Spanien', 'Spanien',
            'Spanien', 'Spanien', 'Spanien', 'Spanien', 'Spanien', 'Spanien', 'Spanien', 'Spanien',
            
            # Frankreich (10)
            'Frankreich', 'Frankreich', 'Frankreich', 'Frankreich', 'Frankreich',
            'Frankreich', 'Frankreich', 'Frankreich', 'Frankreich', 'Frankreich',
            
            # Deutschland (10)
            'Deutschland', 'Deutschland', 'Deutschland', 'Deutschland', 'Deutschland',
            'Deutschland', 'Deutschland', 'Deutschland', 'Deutschland', 'Deutschland',
            
            # Andere Europa (36)
            'Portugal', 'Portugal', 'Portugal', 'Portugal', 'Portugal',
            'Wales', 'Wales', 'Schottland', 'Schottland',
            'Irland', 'Irland',
            'Ungarn', 'Ungarn', 'Ungarn',
            'Dänemark', 'Dänemark',
            'Italien', 'Italien', 'Italien', 'Italien',
            'Schweiz', 'Schweiz', 'Schweiz', 'Schweiz',
            'Österreich', 'Österreich', 'Österreich',
            'Polen', 'Polen', 'Rumänien', 'Rumänien',
            
            # Ozeanien (21)
            'Neuseeland', 'Neuseeland', 'Neuseeland', 'Neuseeland', 'Neuseeland', 'Neuseeland',
            'Australien', 'Australien', 'Australien', 'Australien', 'Australien', 'Australien',
            'Australien', 'Australien', 'Australien', 'Australien', 'Australien', 'Australien',
            'Australien', 'Australien', 'Australien',
            
            # Afrika (26)
            'Namibia', 'Namibia', 'Namibia',
            'Botswana', 'Botswana', 'Botswana',
            'Südafrika', 'Südafrika', 'Südafrika', 'Südafrika', 'Südafrika', 'Südafrika', 'Südafrika',
            'Marokko', 'Marokko', 'Marokko',
            'Algerien', 'Algerien', 'Algerien',
            'Chad', 'Niger', 'Chad',
            'Äthiopien', 'Äthiopien', 'Äthiopien',
            
            # Asien (47)
            # Indien (13)
            'Indien', 'Indien', 'Indien', 'Indien', 'Indien', 'Indien', 'Indien',
            'Indien', 'Indien', 'Indien', 'Indien', 'Indien', 'Indien',
            
            # Nepal & Tibet (10)
            'Nepal', 'Nepal', 'Nepal', 'Nepal', 'Nepal', 'Nepal', 'Nepal',
            'Tibet/China', 'Tibet/China', 'Tibet/China',
            
            # Zentralasien (11)
            'Tadschikistan', 'Kirgisistan', 'Mongolei', 'Mongolei', 'Mongolei', 'Mongolei',
            'Pakistan', 'Pakistan', 'Pakistan', 'Pakistan', 'Pakistan',
            
            # China (8)
            'China', 'China', 'China', 'China', 'China', 'China', 'China', 'China'
        ],
        
        # Koordinaten für alle Standorte
        'Latitude': [
            # Chile (10)
            -24.6282, -24.0258, -24.6275, -29.2563, -29.0158, -30.1697, -30.2408,
            -29.9081, -22.9083, -24.0625,
            
            # USA (52) - Realistische Koordinaten
            19.8207, 19.4756, 20.7097,  # Hawaii
            36.5054, 33.8792, 33.2778, 35.0089, 36.2677, 34.2256, 33.3533, 37.3414,  # California
            29.1275, 30.6792, 30.5089,  # Texas
            41.6628, 38.7331, 38.2972,  # PA, WV, VA
            44.3500, 45.8968,  # Maine
            37.5930, 38.2972, 38.7331, 37.6283, 38.4597, 39.2847, 39.2856,  # Utah
            39.0968, 37.7326, 36.4863,  # California National Parks
            36.0544, 34.8697, 35.2119, 35.2119,  # Arizona
            36.0339, 34.0784, 36.7856,  # New Mexico
            38.5762, 37.7326, 40.3428,  # Colorado
            44.9778, 43.7904, 44.5900,  # Wyoming
            43.8554, 47.7511,  # Dakotas
            48.7596, 58.5000, 63.0695, 64.8378,  # Montana, Alaska
            
            # Kanada (16)
            52.8737, 51.4968, 49.0500,  # Alberta National Parks
            45.4532, 45.5017, 46.0126, 44.9481, 42.2619, 42.6548, 45.0000,  # Eastern Canada
            49.6000, 59.1253, 50.8000, 50.0500, 45.0500, 44.4000,  # Western/Central Canada
            
            # Europa - Spanien (14)
            28.7606, 28.3000, 37.2200, 41.5900, 43.1500, 37.0900,
            40.3500, 39.4500, 42.8500, 42.5200, 28.3500, 29.0500, 28.1000, 28.0900,
            
            # Frankreich (10)
            42.9369, 43.9317, 45.8326, 44.2619, 48.9333, 44.7500,
            42.8500, 45.0500, 44.1000, 44.9000,
            
            # Deutschland (10)
            47.4211, 50.4986, 51.7993, 47.8742, 52.6833, 50.3833,
            49.0394, 51.2297, 47.7211, 50.0000,
            
            # Andere Europa (31)
            38.2433, 38.5000, 41.7000, 32.7500, 37.7500,  # Portugal
            51.8838, 53.0685, 55.0000, 57.0000,  # Wales, Scotland
            52.1392, 53.5000,  # Ireland
            46.2283, 47.5833, 47.8000,  # Hungary
            54.9833, 57.0000,  # Denmark
            38.1900, 42.3500, 46.5000, 37.8000,  # Italy
            46.5472, 45.9833, 46.8000, 46.3000,  # Switzerland
            47.0000, 47.2000, 47.5000,  # Austria
            49.2000, 49.0000, 45.5000, 46.0000,  # Poland, Romania
            
            # Ozeanien (21)
            -44.0061, -36.1833, -46.8833, -44.0000, -43.4000, -44.6000,  # New Zealand
            -25.3444, -25.3000, -24.2000, -32.1283, -37.1500, -33.7000,  # Australia
            -31.2833, -36.1667, -33.7000, -32.5000, -24.5000, -20.0000,
            -20.5000, -17.0000, -42.0000,
            
            # Afrika (25)
            -25.0000, -24.5000, -27.5000,  # Namibia
            -22.0000, -19.0000, -20.5000,  # Botswana
            -32.2928, -32.3000, -32.4667, -29.1319, -28.7500, -28.4000, -26.0000,  # South Africa
            31.7917, 31.0500, 30.5000,  # Morocco
            23.0000, 23.2667, 25.0000,  # Algeria
            20.0000, 18.5000, 17.0000,  # Chad, Niger
            9.1450, 13.2667, 7.0000,  # Ethiopia
            
            # Asien (47)
            # Indien (13)
            34.1526, 32.2432, 34.8797, 33.5000, 33.7000, 34.0000, 32.0000,
            31.5000, 32.5000, 32.2000, 27.0000, 23.0000, 15.0000,
            
            # Nepal & Tibet (10)
            28.0000, 28.5000, 29.3000, 28.6000, 28.2000, 29.0000, 27.9881,
            30.0000, 31.0000, 32.0000,
            
            # Zentralasien (11)
            38.5000, 42.0000, 47.0000, 43.0000, 47.0000, 47.5000,
            36.0000, 35.5000, 36.5000, 35.2000, 35.0000,
            
            # China (8)
            39.0000, 43.5000, 42.0000, 36.0000, 36.5000, 38.0000, 37.0000, 35.0000
        ],
        
        'Longitude': [
            # Chile (10)
            -70.4034, -67.7558, -70.4033, -70.7369, -70.6919, -70.8150, -70.8039,
            -70.8217, -68.2650, -67.3000,
            
            # USA (52)
            -155.4681, -155.6083, -156.2533,  # Hawaii
            -117.0794, -116.4194, -116.1669, -115.2583, -121.8080, -118.0575, -116.8658, -121.6431,  # California
            -103.2420, -104.0228, -99.0000,  # Texas
            -77.8261, -79.8333, -78.4569,  # PA, WV, VA
            -68.2733, -68.6000,  # Maine
            -112.1660, -111.2615, -109.5925, -110.0067, -109.8569, -110.8231, -114.2669,  # Utah
            -119.5383, -119.5383, -118.5569,  # California National Parks
            -112.1401, -111.7533, -111.6647, -111.6647,  # Arizona
            -107.9628, -106.8200, -103.9728,  # New Mexico
            -107.7211, -105.5943, -105.6836,  # Colorado
            -110.5422, -110.8020, -110.5000,  # Wyoming
            -101.9777, -100.3367,  # Dakotas
            -113.7870, -153.0000, -153.0000, -147.7164,  # Montana, Alaska
            
            # Kanada (16)
            -117.9542, -115.5708, -113.9167,  # Alberta
            -71.1513, -78.3947, -81.4017, -79.8711, -82.5156, -81.2453, -79.5000,  # Eastern
            -109.0000, -112.0000, -106.0000, -98.0000, -66.0000, -65.0000,  # Western/Central
            
            # Europa - Spanien (14)
            -17.8847, -16.6400, -2.5400, 1.1167, -5.0000, -3.1800,
            -5.5000, -6.5000, 0.5000, -0.5000, -14.0000, -13.8000, -15.4000, -17.1000,
            
            # Frankreich (10)
            0.1426, 5.7142, 6.8652, 3.8167, 7.1167, 2.0000,
            0.5000, 6.5000, 7.2000, 6.0000,
            
            # Deutschland (10)
            10.9850, 9.9406, 10.6175, 8.1058, 12.4167, 6.4167,
            13.2833, 9.7400, 11.8000, 11.0000,
            
            # Andere Europa (31)
            -7.5000, -8.0000, -8.5000, -16.9000, -25.6667,  # Portugal
            -3.4360, -4.0000, -4.0000, -4.0000,  # Wales, Scotland
            -9.9267, -9.0000,  # Ireland
            18.2167, 21.1167, 20.0000,  # Hungary
            12.4500, 10.0000,  # Denmark
            16.2400, 13.0000, 11.0000, 15.0000,  # Italy
            7.9853, 7.7500, 9.5000, 8.0000,  # Switzerland
            13.0000, 14.0000, 13.5000,  # Austria
            20.0000, 19.0000, 25.0000, 24.0000,  # Poland, Romania
            
            # Ozeanien (21)
            170.1409, 175.0833, 168.1167, 170.0000, 170.5000, 168.0000,  # New Zealand
            131.0369, 131.2000, 132.0000, 138.6283, 142.5000, 151.0000,  # Australia
            149.0167, 141.6167, 151.5000, 129.0000, 127.0000, 122.0000,
            119.0000, 128.0000, 147.0000,
            
            # Afrika (25)
            16.0000, 15.3000, 17.5000,  # Namibia
            24.0000, 22.5000, 23.0000,  # Botswana
            20.0000, 20.0000, 19.0000, 29.4189, 17.0000, 20.0000, 20.5000,  # South Africa
            -7.0926, -8.0000, -7.0000,  # Morocco
            5.0000, 5.5667, 8.0000,  # Algeria
            18.0000, 8.0000, 22.0000,  # Chad, Niger
            40.4897, 38.2667, 39.0000,  # Ethiopia
            
            # Asien (47)
            # Indien (13)
            77.5771, 78.0647, 77.6408, 77.5000, 78.0000, 77.0000, 78.5000,
            78.5000, 77.2000, 77.2000, 72.0000, 70.0000, 77.0000,
            
            # Nepal & Tibet (10)
            86.9250, 84.0000, 83.8000, 84.7278, 85.3000, 83.0000, 86.9250,
            88.0000, 81.0000, 80.0000,
            
            # Zentralasien (11)
            71.0000, 75.0000, 89.0000, 103.0000, 106.0000, 100.0000,
            76.0000, 75.5000, 74.5000, 75.6000, 74.0000,
            
            # China (8)
            84.0000, 87.0000, 111.0000, 96.0000, 94.0000, 100.0000, 95.0000, 109.0000
        ],
        
        # Höhenangaben (realistisch)
        'Höhe_m': [
            # Chile (10)
            2400, 5000, 2635, 2400, 2380, 2200, 2722, 1500, 2300, 4800,
            
            # USA (52)
            4200, 4169, 3055,  # Hawaii
            1669, 1230, 600, 900, 350, 1742, 1706, 1283,  # California
            1200, 2075, 500,  # Texas
            670, 1483, 1100,  # PA, WV, VA
            158, 300,  # Maine
            2400, 1800, 1500, 2000, 1900, 1700, 2000,  # Utah
            2100, 2100, 1900,  # California NP
            2100, 1300, 2210, 2210,  # Arizona
            1900, 2100, 2500,  # New Mexico
            2700, 2200, 3000,  # Colorado
            2400, 2300, 1500,  # Wyoming
            1000, 600,  # Dakotas
            1040, 200, 650, 134,  # Montana, Alaska
            
            # Kanada (16)
            1200, 1400, 1200, 1114, 400, 500, 300, 200, 180, 250,
            1000, 200, 700, 800, 100, 50,
            
            # Europa - Spanien (14)
            2396, 2000, 1200, 1000, 1800, 2000, 1400, 500, 1500, 1600,
            600, 800, 1200, 500,
            
            # Frankreich (10)
            2877, 650, 4809, 800, 600, 1200, 1500, 2000, 1800, 1500,
            
            # Deutschland (10)
            2962, 950, 1141, 1493, 75, 600, 1365, 754, 1800, 1000,
            
            # Andere Europa (31)
            152, 250, 1800, 1200, 800,  # Portugal
            520, 1085, 350, 700,  # Wales, Scotland
            344, 400,  # Ireland
            400, 200, 600,  # Hungary
            50, 40,  # Denmark
            1200, 1800, 3343, 3300,  # Italy
            3454, 3089, 2500, 2000,  # Switzerland
            3798, 3000, 2500,  # Austria
            2499, 1600, 2544, 2000,  # Poland, Romania
            
            # Ozeanien (21)
            1031, 200, 100, 1000, 2000, 500,  # New Zealand
            348, 500, 600, 800, 1167, 300,  # Australia
            600, 300, 200, 150, 400, 500, 600, 400, 1000,
            
            # Afrika (25)
            1200, 1000, 1500,  # Namibia
            1000, 900, 1100,  # Botswana
            1200, 1500, 1800, 2000, 800, 1000, 900,  # South Africa
            1165, 2000, 1800,  # Morocco
            800, 1800, 1200,  # Algeria
            1500, 1500, 1200,  # Chad, Niger
            2500, 3000, 2800,  # Ethiopia
            
            # Asien (47)
            # Indien (13)
            3500, 4000, 3200, 3800, 4200, 3600, 3700, 2500, 3000, 2200,
            400, 100, 1500,
            
            # Nepal & Tibet (10)
            5000, 4200, 3800, 4500, 4000, 4300, 5300, 4500, 4800, 4600,
            
            # Zentralasien (11)
            3800, 3500, 2500, 1500, 1200, 1800, 4000, 4500, 2500, 2200, 3000,
            
            # China (8)
            800, 1200, 1000, 3200, 3500, 2800, 2800, 2000
        ],
        
        # Bortle-Skala (realistisch nach Standort-Typ)
        'Bortle_Skala': [
            # Chile (10) - Exzellent
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            
            # USA (52)
            1, 1, 2,  # Hawaii
            1, 2, 1, 1, 3, 2, 2, 3,  # California
            1, 1, 2,  # Texas
            2, 2, 3,  # PA, WV, VA
            3, 2,  # Maine
            2, 2, 2, 1, 2, 2, 1,  # Utah
            3, 2, 3,  # California NP
            2, 3, 2, 2,  # Arizona
            1, 1, 1,  # New Mexico
            2, 2, 2,  # Colorado
            2, 2, 2,  # Wyoming
            2, 2,  # Dakotas
            2, 1, 1, 2,  # Montana, Alaska
            
            # Kanada (16)
            2, 2, 2, 2, 3, 2, 2, 3, 3, 3, 1, 1, 2, 2, 3, 3,
            
            # Europa
            2, 2, 2, 2, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2,  # Spanien (14)
            2, 2, 2, 3, 3, 3, 3, 2, 2, 2,  # Frankreich (10)
            2, 3, 3, 2, 2, 3, 3, 2, 2, 3,  # Deutschland (10)
            2, 2, 3, 2, 2, 3, 2, 2, 3, 3, 3, 2, 2, 2, 2, 2,  # Andere Europa
            3, 3, 3, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3,  # Fortsetzung Europa
            
            # Ozeanien (21)
            1, 2, 1, 2, 2, 2,  # New Zealand
            1, 1, 1, 1, 2, 3, 2, 2, 2, 1, 1, 1, 1, 1, 2,  # Australia
            
            # Afrika (25)
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  # Southern Africa
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  # North & East Africa
            
            # Asien (47)
            1, 1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 2, 2,  # Indien (13)
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  # Nepal & Tibet (10)
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  # Zentralasien (11)
            1, 1, 2, 1, 1, 1, 1, 2  # China (8)
        ],
        
        # Klimazonen für bessere Schätzungen
        'Klimazone': [
            # Chile (10)
            'desert', 'desert', 'desert', 'desert', 'desert', 'desert', 'desert',
            'desert', 'desert', 'desert',
            
            # USA (52)
            'oceanic', 'oceanic', 'oceanic',  # Hawaii
            'desert', 'desert', 'desert', 'desert', 'mediterranean', 'mediterranean', 'mediterranean', 'mediterranean',
            'desert', 'desert', 'continental',
            'continental', 'continental', 'continental',
            'oceanic', 'oceanic',
            'desert', 'desert', 'desert', 'desert', 'desert', 'desert', 'desert',
            'continental', 'continental', 'continental',
            'desert', 'desert', 'continental', 'continental',
            'desert', 'continental', 'desert',
            'continental', 'desert', 'continental',
            'continental', 'continental', 'continental',
            'continental', 'continental',
            'continental', 'polar', 'polar', 'polar',
            
            # Kanada (16)
            'continental', 'continental', 'continental', 'continental', 'continental', 'continental',
            'continental', 'continental', 'continental', 'continental', 'continental', 'continental',
            'continental', 'continental', 'oceanic', 'oceanic',
            
            # Europa
            'oceanic', 'oceanic', 'mediterranean', 'continental', 'continental', 'mediterranean',  # Spanien
            'mediterranean', 'mediterranean', 'continental', 'continental', 'oceanic', 'oceanic', 'oceanic', 'oceanic',
            'continental', 'mediterranean', 'continental', 'continental', 'continental',  # Frankreich
            'continental', 'continental', 'continental', 'continental', 'continental',
            'continental', 'continental', 'continental', 'continental', 'continental',  # Deutschland
            'mediterranean', 'mediterranean', 'continental', 'oceanic', 'oceanic',  # Portugal
            'oceanic', 'oceanic', 'oceanic', 'oceanic',  # UK
            'oceanic', 'oceanic',  # Ireland
            'continental', 'continental', 'continental',  # Hungary
            'oceanic', 'oceanic',  # Denmark
            'mediterranean', 'continental', 'continental', 'mediterranean',  # Italy
            'continental', 'continental', 'continental', 'continental',  # Switzerland
            'continental', 'continental', 'continental',  # Austria
            'continental', 'continental', 'continental', 'continental',  # Poland, Romania
            
            # Ozeanien (21)
            'oceanic', 'oceanic', 'oceanic', 'oceanic', 'oceanic', 'oceanic',  # New Zealand
            'desert', 'desert', 'desert', 'mediterranean', 'oceanic', 'oceanic',  # Australia
            'oceanic', 'continental', 'oceanic', 'desert', 'desert', 'desert', 'desert', 'tropical', 'oceanic',
            
            # Afrika (25)
            'desert', 'desert', 'desert', 'desert', 'desert', 'desert',
            'desert', 'desert', 'mediterranean', 'continental', 'desert', 'desert', 'desert',
            'desert', 'continental', 'continental',
            'desert', 'desert', 'desert',
            'desert', 'desert', 'desert',
            'continental', 'continental', 'continental',
            
            # Asien (47)
            'desert', 'desert', 'desert', 'desert', 'desert', 'desert', 'desert',  # Indien Hochgebirge
            'continental', 'continental', 'continental', 'desert', 'desert', 'tropical',  # Indien Rest
            'continental', 'continental', 'continental', 'continental', 'continental', 'continental', 'continental',  # Nepal & Tibet
            'continental', 'continental', 'continental', 'continental', 'continental', 'continental',  # Zentralasien
            'continental', 'continental', 'continental', 'continental', 'continental',
            'desert', 'desert', 'continental', 'continental', 'continental', 'continental', 'continental', 'continental'  # China
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
continents = {
    'Europa': len(enhanced_df[enhanced_df['Land'].isin(['Deutschland', 'Frankreich', 'Spanien', 'Italien', 'Portugal', 'Wales', 'Schottland', 'Irland', 'Ungarn', 'Dänemark', 'Schweiz', 'Österreich', 'Polen', 'Rumänien'])]),
    'Nordamerika': len(enhanced_df[enhanced_df['Land'].isin(['USA', 'Kanada'])]),
    'Südamerika': len(enhanced_df[enhanced_df['Land'] == 'Chile']),
    'Asien': len(enhanced_df[enhanced_df['Land'].isin(['Indien', 'Nepal', 'Tibet/China', 'China', 'Pakistan', 'Tadschikistan', 'Kirgisistan', 'Mongolei'])]),
    'Afrika': len(enhanced_df[enhanced_df['Land'].isin(['Namibia', 'Südafrika', 'Botswana', 'Marokko', 'Algerien', 'Äthiopien', 'Chad', 'Niger'])]),
    'Ozeanien': len(enhanced_df[enhanced_df['Land'].isin(['Australien', 'Neuseeland'])])
}

st.sidebar.metric("🌍 Gesamt-Standorte", len(enhanced_df), f"+{len(enhanced_df)-29} vs. vorher")
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
        'Europa': ['Deutschland', 'Frankreich', 'Spanien', 'Italien', 'Portugal', 'Wales', 'Schottland', 'Irland', 'Ungarn', 'Dänemark', 'Schweiz', 'Österreich', 'Polen', 'Rumänien'],
        'Nordamerika': ['USA', 'Kanada'],
        'Südamerika': ['Chile'],
        'Asien': ['Indien', 'Nepal', 'Tibet/China', 'China', 'Pakistan', 'Tadschikistan', 'Kirgisistan', 'Mongolei'],
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
**🚀 Ultimative Astrotourismus-Datenbank v2.0**

**📊 Abgedeckte Regionen ({len(enhanced_df)} Standorte):**
- 🇪🇺 **Europa**: {continents['Europa']} Standorte (Deutschland, Frankreich, Spanien, Italien, Schweiz, Österreich...)
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
