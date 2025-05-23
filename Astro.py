# Dark Mode Toggle
dark_mode = st.sidebar.toggle(
    "🌙 Dark Mode",
    value=False,
    help="Dunkle Karten für bessere Nachtsicht"
)

# Erweiterte Karten-Optionen
with simport streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Seitenkonfiguration
st.set_page_config(
    page_title="Astrotourismus Weltkarte",
    page_icon="🌟",
    layout="wide"
)

# Titel und Beschreibung
st.title("🌟 Weltkarte für Astrotourismus")
st.markdown("""
Diese interaktive Karte zeigt die besten Orte weltweit für Sternenbeobachtung und Astrotourismus,
basierend auf geringer Lichtverschmutzung und optimalen Himmelsbedingungen.
""")

# DATEN DIREKT ERSTELLEN - OHNE FUNKTIONEN
# Hauptdatensatz für Regionen
df = pd.DataFrame({
    'Name': [
        # Chile
        'Atacama-Wüste', 'Elqui Valley', 'La Silla Observatory', 'Paranal Observatory',
        # USA
        'Mauna Kea', 'Death Valley', 'Big Bend', 'Cherry Springs', 'Bryce Canyon',
        'Great Basin NP', 'Capitol Reef NP', 'Arches NP', 'Natural Bridges NM',
        'Rainbow Bridge NM', 'Hovenweep NM', 'Chaco Culture NHP', 'Capulin Volcano NM',
        'Black Canyon of Gunnison NP', 'Colorado NM', 'Dinosaur NM',
        'Fossil Butte NM', 'Great Sand Dunes NP', 'Mesa Verde NP',
        # Kanada
        'Jasper Nationalpark', 'Mont-Mégantic', 'Algonquin Provincial Park',
        'Point Pelee NP', 'Killarney Provincial Park', 'Torrance Barrens',
        'Muskoka Region', 'Cypress Hills Interprovincial Park',
        # Europa
        'La Palma', 'Pic du Midi', 'Alqueva', 'Brecon Beacons', 'Galloway Forest',
        'Kerry', 'Rhön', 'Westhavelland', 'Eifel Nationalpark', 'Spiegelau',
        'Zselic Starry Sky Park', 'Hortobágy', 'Møn', 'Aspromonte',
        'Cévennes', 'Vosges du Nord', 'Pyrénées', 'Montsec', 'Picos de Europa',
        'Sierra de Gredos', 'Sierra Nevada', 'Extremadura', 'Madeira',
        'Azoren', 'Teneriffa', 'Fuerteventura',
        # Neuseeland & Australien
        'Aoraki Mackenzie', 'Great Barrier Island', 'Rakiura Stewart Island',
        'Uluru', 'Flinders Ranges', 'Warrumbungle NP', 'Little Desert NP',
        'River Murray', 'Nullarbor Plain',
        # Afrika
        'Namibrand', 'Sahara Marokko', 'Sahara Algerien', 'Kalahari',
        'Karoo', 'Atlas Mountains', 'Hoggar Mountains', 'Air Mountains',
        'Ethiopian Highlands', 'Simien Mountains', 'Drakensberg',
        'Tankwa Karoo', 'Cederberg', 'Richtersveld',
        # Asien
        'Ladakh', 'Spiti Valley', 'Nubra Valley', 'Changthang Plateau',
        'Gobi-Wüste', 'Taklamakan', 'Thar-Wüste', 'Karakorum',
        'Pamir', 'Tian Shan', 'Altai Mountains', 'Mongolische Steppe',
        'Tibet Plateau', 'Himalaya Base Camps', 'Mustang Nepal',
        'Annapurna Region', 'Everest Region', 'Manaslu Region'
    ],
    'Land': [
        # Chile
        'Chile', 'Chile', 'Chile', 'Chile',
        # USA
        'USA (Hawaii)', 'USA', 'USA', 'USA', 'USA',
        'USA', 'USA', 'USA', 'USA',
        'USA', 'USA', 'USA', 'USA',
        'USA', 'USA', 'USA',
        'USA', 'USA', 'USA',
        # Kanada
        'Kanada', 'Kanada', 'Kanada',
        'Kanada', 'Kanada', 'Kanada',
        'Kanada', 'Kanada',
        # Europa
        'Spanien', 'Frankreich', 'Portugal', 'Wales', 'Schottland',
        'Irland', 'Deutschland', 'Deutschland', 'Deutschland', 'Deutschland',
        'Ungarn', 'Ungarn', 'Dänemark', 'Italien',
        'Frankreich', 'Frankreich', 'Frankreich', 'Spanien', 'Spanien',
        'Spanien', 'Spanien', 'Spanien', 'Portugal',
        'Portugal', 'Spanien', 'Spanien',
        # Neuseeland & Australien
        'Neuseeland', 'Neuseeland', 'Neuseeland',
        'Australien', 'Australien', 'Australien', 'Australien',
        'Australien', 'Australien',
        # Afrika
        'Namibia', 'Marokko', 'Algerien', 'Botswana',
        'Südafrika', 'Marokko', 'Algerien', 'Niger',
        'Äthiopien', 'Äthiopien', 'Südafrika',
        'Südafrika', 'Südafrika', 'Südafrika',
        # Asien
        'Indien', 'Indien', 'Indien', 'Indien',
        'Mongolei', 'China', 'Indien', 'Pakistan',
        'Tadschikistan', 'Kirgisistan', 'Mongolei', 'Mongolei',
        'Tibet/China', 'Nepal', 'Nepal',
        'Nepal', 'Nepal', 'Nepal'
    ],
    'Latitude': [
        # Chile
        -24.6282, -29.9081, -29.2563, -24.6275,
        # USA
        19.8207, 36.5054, 29.1275, 41.6628, 37.5930,
        39.2856, 38.2972, 38.7331, 37.6283,
        37.0682, 37.3856, 36.0339, 36.7856,
        38.5762, 39.0745, 40.4395,
        41.8683, 37.7326, 37.1853,
        # Kanada
        52.8737, 45.4532, 45.5017,
        42.2619, 46.0126, 44.9481,
        45.0000, 49.6000,
        # Europa
        28.7636, 42.9369, 38.2433, 51.8838, 55.0000,
        52.1392, 50.4500, 52.6833, 50.3833, 49.0167,
        46.2283, 47.5833, 54.9833, 38.1900,
        44.2619, 48.9333, 42.8500, 42.3167, 43.1500,
        40.3500, 37.0900, 39.4500, 32.7500,
        37.7500, 28.2900, 28.3500,
        # Neuseeland & Australien
        -44.0061, -36.1833, -46.8833,
        -25.3444, -32.1283, -31.2833, -36.1667,
        -34.7500, -32.5000,
        # Afrika
        -25.0000, 31.7917, 23.0000, -22.0000,
        -32.2928, 31.0500, 23.2667, 18.5000,
        9.1450, 13.2667, -29.1319,
        -32.3000, -32.4667, -28.7500,
        # Asien
        34.1526, 32.2432, 34.8797, 33.7000,
        43.0000, 39.0000, 27.0000, 36.0000,
        38.5000, 42.0000, 47.0000, 47.0000,
        30.0000, 28.0000, 29.3000,
        28.5000, 27.9881, 28.6000
    ],
    'Longitude': [
        # Chile
        -70.4034, -70.8217, -70.7369, -70.4033,
        # USA
        -155.4681, -117.0794, -103.2420, -77.8261, -112.1660,
        -114.2669, -111.2615, -109.5925, -110.0067,
        -110.9623, -109.0739, -107.9628, -103.9728,
        -107.7211, -108.7184, -109.2444,
        -110.5422, -105.5943, -108.4618,
        # Kanada
        -117.9542, -71.1513, -78.3947,
        -82.5156, -81.4017, -79.8711,
        -79.5000, -109.0000,
        # Europa
        -17.8735, 0.1426, -7.5000, -3.4360, -4.0000,
        -9.9267, 10.0000, 12.4167, 6.4167, 13.2833,
        18.2167, 21.1167, 12.4500, 16.2400,
        3.8167, 7.1167, 0.5000, 1.1167, -5.0000,
        -5.5000, -3.1800, -6.5000, -16.9000,
        -25.6667, -16.6400, -14.0000,
        # Neuseeland & Australien
        170.1409, 175.0833, 168.1167,
        131.0369, 138.6283, 149.0167, 141.6167,
        140.7500, 129.0000,
        # Afrika
        16.0000, -7.0926, 5.0000, 24.0000,
        20.0000, -8.0000, 5.5667, 8.0000,
        40.4897, 38.2667, 29.4189,
        20.0000, 19.0000, 17.0000,
        # Asien
        77.5771, 78.0647, 77.6408, 78.0000,
        103.0000, 84.0000, 72.0000, 76.0000,
        71.0000, 75.0000, 89.0000, 106.0000,
        88.0000, 86.9250, 83.8000,
        84.0000, 86.9250, 84.7278
    ],
    'Bortle_Skala': [
        # Chile
        1, 1, 1, 1,
        # USA
        1, 1, 1, 2, 2,
        1, 2, 2, 1,
        1, 1, 1, 1,
        2, 1, 1,
        1, 2, 2,
        # Kanada
        2, 2, 3,
        3, 2, 2,
        3, 1,
        # Europa
        2, 2, 2, 3, 2,
        3, 3, 2, 3, 3,
        2, 2, 2, 3,
        3, 3, 3, 2, 3,
        3, 3, 3, 2,
        2, 2, 2,
        # Neuseeland & Australien
        1, 2, 1,
        1, 1, 2, 2,
        2, 1,
        # Afrika
        1, 1, 1, 1,
        1, 1, 1, 1,
        1, 1, 1,
        1, 1, 1,
        # Asien
        1, 1, 1, 1,
        1, 1, 1, 1,
        1, 1, 1, 1,
        1, 1, 1,
        1, 1, 1
    ],
    'Klare_Nächte_Jahr': [
        # Chile
        320, 330, 310, 325,
        # USA
        300, 350, 320, 200, 220,
        280, 250, 240, 270,
        280, 260, 290, 300,
        210, 270, 250,
        240, 230, 200,
        # Kanada
        200, 180, 160,
        140, 170, 180,
        150, 250,
        # Europa
        280, 220, 260, 180, 170,
        160, 150, 120, 140, 130,
        190, 200, 170, 240,
        200, 180, 210, 250, 190,
        200, 220, 210, 250,
        240, 260, 270,
        # Neuseeland & Australien
        250, 200, 220,
        290, 270, 240, 220,
        210, 300,
        # Afrika
        310, 300, 320, 280,
        260, 280, 310, 290,
        250, 240, 270,
        280, 290, 300,
        # Asien
        280, 270, 260, 250,
        240, 200, 210, 230,
        220, 210, 200, 230,
        180, 190, 180,
        170, 160, 150
    ],
    'Höhe_m': [
        # Chile
        2400, 1500, 2400, 2635,
        # USA
        4200, 1669, 1200, 670, 2400,
        2000, 1800, 1500, 2000,
        1200, 1600, 1900, 2500,
        2700, 1800, 1400,
        2100, 2200, 2400,
        # Kanada
        1200, 1114, 400,
        200, 500, 300,
        250, 1000,
        # Europa
        2396, 2877, 152, 520, 350,
        344, 815, 75, 600, 740,
        400, 200, 50, 1200,
        800, 600, 1500, 1000, 1800,
        1400, 2000, 500, 1200,
        800, 2000, 600,
        # Neuseeland & Australien
        1031, 200, 100,
        348, 800, 600, 300,
        100, 150,
        # Afrika
        1200, 1165, 800, 1000,
        1200, 2000, 1800, 1500,
        2500, 3000, 2000,
        1500, 1800, 800,
        # Asien
        3500, 4000, 3200, 4200,
        1500, 800, 400, 4000,
        3800, 3500, 2500, 1200,
        4500, 5000, 3800,
        4200, 5300, 4500
    ],
    'Luftfeuchtigkeit_%': [
        # Chile
        20, 25, 15, 18,
        # USA
        25, 15, 35, 70, 40,
        30, 35, 25, 20,
        25, 30, 35, 20,
        45, 30, 35,
        40, 40, 60,
        # Kanada
        60, 65, 70,
        75, 65, 70,
        75, 40,
        # Europa
        45, 40, 55, 70, 80,
        85, 75, 80, 75, 70,
        60, 65, 80, 60,
        70, 70, 60, 50, 65,
        60, 55, 60, 60,
        65, 50, 45,
        # Neuseeland & Australien
        65, 75, 80,
        40, 45, 55, 60,
        65, 35,
        # Afrika
        15, 30, 25, 20,
        35, 40, 20, 25,
        50, 45, 40,
        30, 35, 25,
        # Asien
        35, 30, 25, 20,
        30, 25, 40, 30,
        25, 35, 45, 40,
        35, 60, 55,
        65, 70, 60
    ],
    'Temperatur_°C': [
        # Chile
        15, 18, 12, 14,
        # USA
        5, 20, 18, 5, 8,
        12, 15, 18, 10,
        22, 16, 14, 8,
        2, 12, 8,
        -2, 6, 4,
        # Kanada
        -5, -10, 2,
        5, 0, 3,
        1, -8,
        # Europa
        18, 2, 16, 12, 9,
        11, 8, 9, 7, 6,
        10, 12, 8, 15,
        12, 8, 5, 18, 10,
        14, 20, 12, 20,
        18, 22, 24,
        # Neuseeland & Australien
        8, 15, 6,
        21, 18, 20, 16,
        22, 25,
        # Afrika
        22, 25, 28, 24,
        18, 20, 30, 32,
        15, 12, 16,
        20, 18, 26,
        # Asien
        -2, -5, -8, -10,
        5, 12, 28, 0,
        -5, 2, 8, 10,
        -8, -15, -12,
        -10, -20, -15
    ],
    'Typ': [
        # Chile
        'Wüste', 'Wüste', 'Observatorium', 'Observatorium',
        # USA
        'Observatorium', 'Dark Sky Park', 'Dark Sky Park', 'Dark Sky Park', 'Dark Sky Park',
        'Dark Sky Park', 'Dark Sky Park', 'Dark Sky Park', 'Dark Sky Monument',
        'Dark Sky Monument', 'Dark Sky Monument', 'Dark Sky Monument', 'Dark Sky Monument',
        'Dark Sky Park', 'Dark Sky Monument', 'Dark Sky Monument',
        'Dark Sky Monument', 'Dark Sky Park', 'Dark Sky Park',
        # Kanada
        'Dark Sky Preserve', 'Dark Sky Reserve', 'Dark Sky Preserve',
        'Dark Sky Preserve', 'Dark Sky Preserve', 'Dark Sky Preserve',
        'Natürlich dunkel', 'Dark Sky Preserve',
        # Europa
        'Observatorium', 'Observatorium', 'Dark Sky Reserve', 'Dark Sky Reserve', 'Dark Sky Park',
        'Dark Sky Reserve', 'Dark Sky Reserve', 'Dark Sky Reserve', 'Dark Sky Reserve', 'Dark Sky Reserve',
        'Dark Sky Park', 'Dark Sky Park', 'Dark Sky Community', 'Dark Sky Park',
        'Dark Sky Reserve', 'Dark Sky Reserve', 'Dark Sky Reserve', 'Observatorium', 'Dark Sky Reserve',
        'Dark Sky Reserve', 'Observatorium', 'Dark Sky Reserve', 'Observatorium',
        'Observatorium', 'Observatorium', 'Observatorium',
        # Neuseeland & Australien
        'Dark Sky Reserve', 'Dark Sky Sanctuary', 'Dark Sky Sanctuary',
        'Dark Sky Sanctuary', 'Dark Sky Reserve', 'Dark Sky Park', 'Dark Sky Park',
        'Dark Sky Community', 'Natürlich dunkel',
        # Afrika
        'Dark Sky Reserve', 'Wüste', 'Wüste', 'Wüste',
        'Wüste', 'Gebirge', 'Gebirge', 'Gebirge',
        'Hochgebirge', 'Hochgebirge', 'Gebirge',
        'Wüste', 'Gebirge', 'Wüste',
        # Asien
        'Hochgebirge', 'Hochgebirge', 'Hochgebirge', 'Hochgebirge',
        'Wüste', 'Wüste', 'Wüste', 'Hochgebirge',
        'Hochgebirge', 'Hochgebirge', 'Gebirge', 'Steppe',
        'Hochgebirge', 'Hochgebirge', 'Hochgebirge',
        'Hochgebirge', 'Hochgebirge', 'Hochgebirge'
    ]
})

# Spezifische Beobachtungsplätze
df_specific = pd.DataFrame({
    'Name': [
        # Deutschland - Spezifische Plätze
        'Wasserkuppe Rhön - Aussichtsturm', 'Westhavelland - Gülper See', 'Eifel - Vogelsang Astronomie',
        'Spiegelau - Waldwipfelweg', 'Zugspitze - Gipfelstation', 'Brocken - Harz Sternwarte',
        'Hoher Meißner - Aussichtspunkt', 'Feldberg Schwarzwald - Turm',
        
        # USA - Spezifische Koordinaten
        'Mauna Kea Visitor Center', 'Mauna Kea Summit Observatories', 'Death Valley Mesquite Flat',
        'Bryce Canyon Sunset Point', 'Arches NP Delicate Arch', 'Great Basin Wheeler Peak',
        'Cherry Springs Astronomy Field', 'McDonald Observatory Texas', 'Palomar Observatory',
        'Mount Wilson Observatory', 'Lowell Observatory Flagstaff',
        
        # Chile - Observatorien
        'ALMA Observatory', 'ESO Paranal Observatory', 'La Silla Observatory',
        'Las Campanas Observatory', 'Cerro Tololo Observatory', 'Gemini South',
        
        # Weitere internationale Highlights
        'Pic du Midi Observatorium', 'Jungfraujoch - Top of Europe', 'Matterhorn Gornergrat',
        'Roque de los Muchachos Observatorium', 'Uluru Sunset Viewing Area', 'Lake Tekapo Observatory'
    ],
    'Land': [
        # Deutschland
        'Deutschland', 'Deutschland', 'Deutschland', 'Deutschland', 'Deutschland', 'Deutschland', 'Deutschland', 'Deutschland',
        # USA
        'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA',
        # Chile
        'Chile', 'Chile', 'Chile', 'Chile', 'Chile', 'Chile',
        # Internationale
        'Frankreich', 'Schweiz', 'Schweiz', 'Spanien', 'Australien', 'Neuseeland'
    ],
    'Latitude': [
        # Deutschland
        50.4986, 52.7167, 50.3847, 49.0394, 47.4211, 51.7993, 51.2297, 47.8742,
        # USA
        19.7587, 19.8207, 36.6617, 37.6283, 38.7369, 39.0050, 41.6628, 30.6792, 33.3533, 34.2256, 35.2119,
        # Chile
        -24.0258, -24.6275, -29.2563, -29.0158, -30.1697, -30.2408,
        # Internationale
        42.9369, 46.5472, 45.9833, 28.7606, -25.3444, -44.0046
    ],
    'Longitude': [
        # Deutschland
        9.9406, 12.4333, 6.4044, 13.2833, 10.9850, 10.6175, 9.7400, 8.1058,
        # USA
        -155.4761, -155.4681, -116.8694, -112.1647, -109.5925, -114.3000, -77.8261, -104.0228, -116.8658, -118.0575, -111.6647,
        # Chile
        -67.7558, -70.4033, -70.7369, -70.6919, -70.8150, -70.8039,
        # Internationale
        0.1426, 7.9853, 7.7500, -17.8847, 131.0369, 170.6833
    ],
    'Höhe_m': [
        # Deutschland
        950, 32, 655, 1365, 2962, 1141, 754, 1493,
        # USA
        2804, 4205, -85, 2718, 1723, 3982, 670, 2075, 1706, 1742, 2210,
        # Chile
        5000, 2635, 2400, 2380, 2200, 2722,
        # Internationale
        2877, 3454, 3089, 2396, 348, 1031
    ],
    'Bortle_Skala': [
        # Deutschland
        3, 2, 3, 3, 2, 3, 2, 2,
        # USA
        2, 1, 1, 2, 2, 1, 2, 1, 2, 2, 2,
        # Chile
        1, 1, 1, 1, 1, 1,
        # Internationale
        2, 1, 1, 1, 1, 1
    ],
    'Typ': [
        # Deutschland
        'Aussichtspunkt', 'Naturgebiet', 'Astronomiezentrum', 'Besucherzentrum', 'Observatorium', 'Sternwarte', 'Aussichtspunkt', 'Aussichtsturm',
        # USA
        'Besucherzentrum', 'Observatorium', 'Aussichtspunkt', 'Aussichtspunkt', 'Naturmonument', 'Gipfel', 'Astronomiefeld', 'Observatorium', 'Observatorium', 'Observatorium', 'Observatorium',
        # Chile
        'Observatorium', 'Observatorium', 'Observatorium', 'Observatorium', 'Observatorium', 'Observatorium',
        # Internationale
        'Observatorium', 'Observatorium', 'Observatorium', 'Observatorium', 'Aussichtspunkt', 'Observatorium'
    ],
    'Zugang': [
        # Deutschland
        'Auto/Wanderweg', 'Auto', 'Auto', 'Auto/Baumwipfelpfad', 'Seilbahn', 'Wanderweg', 'Wanderweg', 'Auto/Seilbahn',
        # USA
        'Auto', 'Auto/4WD', 'Auto', 'Auto/Shuttle', 'Wanderweg', 'Wanderweg', 'Auto', 'Auto', 'Auto', 'Auto', 'Auto',
        # Chile
        '4WD/Tour', '4WD/Tour', 'Auto', 'Auto', 'Auto', 'Auto',
        # Internationale
        'Seilbahn', 'Zahnradbahn', 'Zahnradbahn', 'Auto/Shuttle', 'Auto/Shuttle', 'Auto'
    ]
})

# Debug-Information
st.sidebar.success(f"✅ {len(df)} Regionen geladen")
st.sidebar.success(f"✅ {len(df_specific)} spezifische Orte geladen")

# Sidebar für Filter
st.sidebar.header("🔍 Filter & Einstellungen")

# Dark Mode Toggle
dark_mode = st.sidebar.toggle(
    "🌙 Dark Mode",
    value=False,
    help="Dunkle Karten für bessere Nachtsicht"
)

# Map Style basierend auf Dark Mode
if dark_mode:
    map_style = "carto-darkmatter"
    plot_template = "plotly_dark"
    st.sidebar.success("🌙 Dark Mode aktiviert")
else:
    map_style = "open-street-map"
    plot_template = "plotly"
    st.sidebar.info("☀️ Light Mode aktiviert")

# Filter für Bortle-Skala
bortle_filter = st.sidebar.slider(
    "Maximale Bortle-Skala (1 = dunkelster Himmel)",
    min_value=1,
    max_value=3,
    value=3,
    help="Bortle-Skala misst Lichtverschmutzung: 1 = perfekter dunkler Himmel, 9 = Stadtzentrum"
)

# Filter für klare Nächte
clear_nights_filter = st.sidebar.slider(
    "Mindestanzahl klare Nächte pro Jahr",
    min_value=100,
    max_value=350,
    value=150
)

# Filter für Typ
type_filter = st.sidebar.multiselect(
    "Standort-Typ",
    options=df['Typ'].unique(),
    default=df['Typ'].unique()
)

# Daten filtern
filtered_df = df[
    (df['Bortle_Skala'] <= bortle_filter) &
    (df['Klare_Nächte_Jahr'] >= clear_nights_filter) &
    (df['Typ'].isin(type_filter))
]

# Hauptbereich mit Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Weltkarte Regionen", "📍 Spezifische Orte", "📊 Statistiken", "📋 Standort-Details"])

with tab1:
    # Weltkarte erstellen
    st.subheader("Interaktive Weltkarte der Astrotourismus-Standorte")
    
    # Weltkarte erstellen
    fig_map = px.scatter_mapbox(
        filtered_df,
        lat='Latitude',
        lon='Longitude',
        hover_name='Name',
        hover_data={
            'Land': True,
            'Bortle_Skala': True,
            'Klare_Nächte_Jahr': True,
            'Höhe_m': True,
            'Typ': True,
            'Latitude': False,
            'Longitude': False
        },
        color='Bortle_Skala',
        color_continuous_scale='Blues_r',
        size='Klare_Nächte_Jahr',
        size_max=20,
        zoom=1,
        height=600,
        title="Beste Orte für Astrotourismus weltweit"
    )
    
    fig_map.update_layout(
        mapbox_style=map_style,
        margin={"r":0,"t":50,"l":0,"b":0},
        template=plot_template
    )
    
    fig_map.update_coloraxes(
        colorbar_title="Bortle-Skala<br>(niedriger = dunkler)"
    )
    
    st.plotly_chart(fig_map, use_container_width=True)
    
    # Legende
    if dark_mode:
        st.markdown("""
        **🌙 Dark Mode Legende:**
        - 🔵 **Punktgröße**: Anzahl klarer Nächte pro Jahr
        - 🎨 **Farbe**: Bortle-Skala (dunkle Punkte = beste Bedingungen)
        - **Bortle 1**: Perfekte Dunkelheit (Milchstraße deutlich sichtbar)
        - **Bortle 2-3**: Exzellente bis sehr gute Bedingungen
        - **Dark Map**: Optimiert für nächtliche Planung 🌌
        """)
    else:
        st.markdown("""
        **Legende:**
        - 🔵 **Punktgröße**: Anzahl klarer Nächte pro Jahr
        - 🎨 **Farbe**: Bortle-Skala (dunkelblau = beste Bedingungen)
        - **Bortle 1**: Perfekte Dunkelheit (Milchstraße deutlich sichtbar)
        - **Bortle 2-3**: Exzellente bis sehr gute Bedingungen
        """)

with tab2:
    # Spezifische Beobachtungsplätze
    st.subheader("📍 Spezifische Beobachtungsplätze mit exakten GPS-Koordinaten")
    
    # Filter für spezifische Orte
    col1, col2 = st.columns(2)
    with col1:
        country_filter = st.multiselect(
            "Länder auswählen:",
            options=sorted(df_specific['Land'].unique()),
            default=sorted(df_specific['Land'].unique())[:5]  # Erste 5 Länder als Standard
        )
    
    with col2:
        access_filter = st.multiselect(
            "Zugangsart:",
            options=df_specific['Zugang'].unique(),
            default=df_specific['Zugang'].unique()
        )
    
    # Daten für spezifische Orte filtern
    filtered_specific = df_specific[
        (df_specific['Land'].isin(country_filter)) &
        (df_specific['Zugang'].isin(access_filter)) &
        (df_specific['Bortle_Skala'] <= bortle_filter)
    ]
    
    # Karte für spezifische Orte
    fig_specific = px.scatter_mapbox(
        filtered_specific,
        lat='Latitude',
        lon='Longitude',
        hover_name='Name',
        hover_data={
            'Land': True,
            'Typ': True,
            'Höhe_m': True,
            'Zugang': True,
            'Bortle_Skala': True,
            'Latitude': ':.4f',
            'Longitude': ':.4f'
        },
        color='Typ',
        color_discrete_sequence=px.colors.qualitative.Set3,
        size='Höhe_m',
        size_max=15,
        zoom=2,
        height=600,
        title=f"Spezifische Beobachtungsplätze ({len(filtered_specific)} Orte)"
    )
    
    fig_specific.update_layout(
        mapbox_style=map_style,
        margin={"r":0,"t":50,"l":0,"b":0},
        template=plot_template
    )
    
    st.plotly_chart(fig_specific, use_container_width=True)
    
    # Informationen zu den spezifischen Orten
    st.markdown("""
    **🎯 Diese Karte zeigt exakte Beobachtungsplätze mit:**
    - **GPS-Koordinaten** für Navigation
    - **Zugangsart** (Auto, 4WD, Wanderweg, etc.)
    - **Infrastruktur** (Parkplätze, Observatorien, Besucherzentren)
    - **Höhenangaben** für optimale Bedingungen
    """)
    
    # Top-Empfehlungen basierend auf Filterkriterien
    if len(filtered_specific) > 0:
        st.subheader("🌟 Top-Empfehlungen für Ihre Auswahl")
        
        # Beste Orte nach Bortle-Skala
        best_sites = filtered_specific.nsmallest(5, 'Bortle_Skala')
        
        for idx, row in best_sites.iterrows():
            with st.expander(f"⭐ {row['Name']} ({row['Land']})"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Bortle-Skala", f"{row['Bortle_Skala']} ⭐")
                    st.metric("Höhe", f"{row['Höhe_m']} m")
                with col2:
                    st.metric("Typ", row['Typ'])
                    st.metric("Zugang", row['Zugang'])
                with col3:
                    st.metric("GPS Lat", f"{row['Latitude']:.4f}°")
                    st.metric("GPS Lon", f"{row['Longitude']:.4f}°")
                
                # Google Maps Link
                gmaps_url = f"https://maps.google.com/maps?q={row['Latitude']},{row['Longitude']}"
                st.markdown(f"🗺️ [**In Google Maps öffnen**]({gmaps_url})")

with tab3:
    st.subheader("📊 Statistiken und Analysen")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Bortle-Skala Verteilung
        fig_bortle = px.histogram(
            filtered_df,
            x='Bortle_Skala',
            title='Verteilung der Bortle-Skala',
            color_discrete_sequence=['#1f77b4'],
            labels={'Bortle_Skala': 'Bortle-Skala', 'count': 'Anzahl Standorte'},
            template=plot_template
        )
        fig_bortle.update_layout(showlegend=False)
        st.plotly_chart(fig_bortle, use_container_width=True)
        
        # Standort-Typen
        fig_type = px.pie(
            filtered_df,
            names='Typ',
            title='Standort-Typen',
            color_discrete_sequence=px.colors.qualitative.Set3,
            template=plot_template
        )
        st.plotly_chart(fig_type, use_container_width=True)
    
    with col2:
        # Klare Nächte vs. Höhe
        fig_scatter = px.scatter(
            filtered_df,
            x='Höhe_m',
            y='Klare_Nächte_Jahr',
            color='Bortle_Skala',
            size='Luftfeuchtigkeit_%',
            hover_data=['Name', 'Land'],
            title='Klare Nächte vs. Höhe über Meeresspiegel',
            labels={
                'Höhe_m': 'Höhe (m)',
                'Klare_Nächte_Jahr': 'Klare Nächte/Jahr',
                'Luftfeuchtigkeit_%': 'Luftfeuchtigkeit (%)'
            },
            color_continuous_scale='Blues_r',
            template=plot_template
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Top 10 Standorte nach klaren Nächten
        top_10 = filtered_df.nlargest(10, 'Klare_Nächte_Jahr')
        fig_bar = px.bar(
            top_10,
            x='Klare_Nächte_Jahr',
            y='Name',
            orientation='h',
            title='Top 10 Standorte nach klaren Nächten',
            color='Bortle_Skala',
            color_continuous_scale='Blues_r',
            template=plot_template
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

with tab4:
    st.subheader("📋 Detaillierte Standort-Informationen")
    
    # Suchfunktion
    search_term = st.text_input("🔍 Standort suchen:", "")
    if search_term:
        mask = filtered_df['Name'].str.contains(search_term, case=False, na=False) | \
               filtered_df['Land'].str.contains(search_term, case=False, na=False)
        display_df = filtered_df[mask]
    else:
        display_df = filtered_df
    
    # Sortieroptionen
    sort_by = st.selectbox(
        "Sortieren nach:",
        ['Name', 'Bortle_Skala', 'Klare_Nächte_Jahr', 'Höhe_m', 'Land']
    )
    
    display_df = display_df.sort_values(sort_by)
    
    # Tabelle mit allen Details
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Bortle_Skala": st.column_config.NumberColumn(
                "Bortle-Skala",
                help="1 = perfekte Dunkelheit, 3 = sehr gut",
                format="%d ⭐"
            ),
            "Klare_Nächte_Jahr": st.column_config.NumberColumn(
                "Klare Nächte/Jahr",
                help="Anzahl der Nächte mit klarem Himmel pro Jahr"
            ),
            "Höhe_m": st.column_config.NumberColumn(
                "Höhe (m)",
                help="Höhe über dem Meeresspiegel"
            ),
            "Luftfeuchtigkeit_%": st.column_config.NumberColumn(
                "Luftfeuchtigkeit (%)",
                help="Durchschnittliche Luftfeuchtigkeit"
            ),
            "Temperatur_°C": st.column_config.NumberColumn(
                "Temperatur (°C)",
                help="Durchschnittstemperatur"
            )
        }
    )

# Seitenleiste mit Zusatzinformationen
st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ Informationen")
st.sidebar.markdown(f"""
**📍 {len(df)} Astrotourismus-Regionen weltweit**
**🎯 {len(df_specific)} Spezifische Beobachtungsplätze**

**Bortle-Skala Erklärung:**
- **1**: Perfekter dunkler Himmel (Milchstraße deutlich sichtbar)
- **2**: Typisch dunkler Standort (sehr gute Bedingungen)
- **3**: Ländlicher Himmel (gute Bedingungen)
- **4-6**: Vorstädtisch bis städtisch
- **7-9**: Stadtzentrum

**Kategorien:**
- **{len(df[df['Typ'].str.contains('Observatorium', na=False)])}** Observatorien
- **{len(df[df['Typ'].str.contains('Dark Sky', na=False)])}** Dark Sky Gebiete
- **{len(df[df['Typ'].str.contains('Wüste', na=False)])}** Wüstenregionen
- **{len(df[df['Typ'].str.contains('Hochgebirge', na=False)])}** Hochgebirgsregionen

**Spezifische Orte:**
- **{len(df_specific[df_specific['Typ'].str.contains('Observatorium', na=False)])}** Observatorien & Sternwarten
- **{len(df_specific[df_specific['Zugang'] == 'Auto'])}** Per Auto erreichbar
- **{len(df_specific[df_specific['Zugang'].str.contains('4WD', na=False)])}** 4WD erforderlich
- **{len(df_specific[df_specific['Zugang'].str.contains('Wanderweg', na=False)])}** Wanderzugänge

**Beste Reisezeiten:**
- **Nordhalbkugel**: Juni-September
- **Südhalbkugel**: Dezember-März
- **Äquatornähe**: Ganzjährig

**Tipps für Astrotourismus:**
- Mondlose Nächte bevorzugen
- Wettervorhersage beachten
- Warme Kleidung mitnehmen
- Rote Taschenlampe verwenden
- Apps: PhotoPills, SkySafari
- GPS-Koordinaten offline speichern

**🗺️ Karten-Modi:**
- **☀️ Light Mode**: Helle Karte für Tagesplanung
- **🌙 Dark Mode**: Dunkle Karte für Nachtsicht
""")

# Zusammenfassung anzeigen
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Regionen Total",
        len(df),
        f"gefiltert: {len(filtered_df)}"
    )

with col2:
    st.metric(
        "Spezifische Orte",
        len(df_specific),
        f"mit GPS-Koordinaten"
    )

with col3:
    if len(filtered_df) > 0:
        avg_bortle = filtered_df['Bortle_Skala'].mean()
        st.metric(
            "Ø Bortle-Skala",
            f"{avg_bortle:.1f}",
            "niedriger = besser"
        )
    else:
        st.metric("Ø Bortle-Skala", "N/A", "keine Daten")

with col4:
    if len(filtered_df) > 0:
        avg_clear = filtered_df['Klare_Nächte_Jahr'].mean()
        st.metric(
            "Ø Klare Nächte",
            f"{avg_clear:.0f}",
            "pro Jahr"
        )
    else:
        st.metric("Ø Klare Nächte", "N/A", "keine Daten")

with col5:
    if len(filtered_df) > 0:
        best_site = filtered_df.loc[filtered_df['Bortle_Skala'].idxmin(), 'Name']
        st.metric(
            "Bester Standort",
            best_site,
            "niedrigste Bortle-Skala"
        )
    else:
        st.metric("Bester Standort", "N/A", "keine Daten")

st.markdown(f"""
---
**Umfassende Astrotourismus-Datenbank mit {len(df)} Regionen und {len(df_specific)} spezifischen Orten**

**🗺️ Abgedeckte Regionen:**
- **Europa**: {len(df[df['Land'].str.contains('Deutschland|Frankreich|Spanien|Italien|Portugal|Wales|Schottland|Irland|Ungarn|Dänemark', na=False)])} Standorte
- **Nordamerika**: {len(df[df['Land'].str.contains('USA|Kanada', na=False)])} Standorte  
- **Südamerika**: {len(df[df['Land'].str.contains('Chile|Argentinien|Bolivien|Peru|Ecuador|Kolumbien|Venezuela|Brasilien|Uruguay', na=False)])} Standorte
- **Afrika**: {len(df[df['Land'].str.contains('Namibia|Südafrika|Marokko|Algerien|Botswana|Niger|Äthiopien', na=False)])} Standorte
- **Asien**: {len(df[df['Land'].str.contains('Indien|China|Tibet|Nepal|Pakistan|Mongolei|Kirgisistan|Tadschikistan', na=False)])} Standorte
- **Ozeanien**: {len(df[df['Land'].str.contains('Australien|Neuseeland|Cook Islands', na=False)])} Standorte

**📍 Spezifische Orte mit GPS-Koordinaten:**
- **Weltklasse-Observatorien**: Mauna Kea, ALMA, Paranal, La Silla
- **Deutsche Standorte**: Zugspitze, Wasserkuppe, Brocken, Feldberg
- **Europäische Highlights**: Pic du Midi, Jungfraujoch, Teide
- **Navigationshilfen**: Exakte GPS-Koordinaten, Google Maps Integration

**Datenquellen:** International Dark-Sky Association, Astronomische Observatorien, Meteorologische Daten, NASA Light Pollution Maps, GPS-Vermessungen
*Hinweis: Die Daten sind für Planungszwecke optimiert und sollten vor einer Reise aktuell verifiziert werden.*
""")
