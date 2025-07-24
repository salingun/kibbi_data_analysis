import pandas as pd
import requests
import folium
from folium.plugins import HeatMap
import time

# 🔑 Replace with your actual key
GOOGLE_API_KEY = "AIzaSyCI6veWMOBWIIaxnn6sVNzRFwAyTJZO530"

# 📄 Load file
df = pd.read_csv("Ontario_users.csv")
df['full_address'] = df[['city', 'postal_code', 'state']].astype(str).agg(', '.join, axis=1)
df['province'] = None

# 🧭 Forward geocode (for missing lat/lng)
def geocode_address(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": GOOGLE_API_KEY}
    r = requests.get(url, params=params)
    if r.status_code == 200:
        res = r.json().get("results", [])
        if res:
            loc = res[0]["geometry"]["location"]
            province = next((c["long_name"] for c in res[0]["address_components"]
                             if "administrative_area_level_1" in c["types"]), None)
            return loc["lat"], loc["lng"], province
    return None, None, None

# 🧭 Reverse geocode (for rows that already have lat/lng)
def reverse_geocode(lat, lng):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"latlng": f"{lat},{lng}", "key": GOOGLE_API_KEY}
    r = requests.get(url, params=params)
    if r.status_code == 200:
        res = r.json().get("results", [])
        if res:
            province = next((c["long_name"] for c in res[0]["address_components"]
                             if "administrative_area_level_1" in c["types"]), None)
            return province
    return None

# 🔍 Geocode missing coordinates
missing_coords = df['lat'].isna() | df['lng'].isna()
for idx, row in df[missing_coords].iterrows():
    print(f"Geocoding address for index {idx}: {row['full_address']}")
    lat, lng, province = geocode_address(row['full_address'])
    df.at[idx, 'lat'] = lat
    df.at[idx, 'lng'] = lng
    df.at[idx, 'province'] = province
    print(f"Result - lat: {lat}, lng: {lng}, province: {province}")
    time.sleep(0.1)

# 🔍 Reverse geocode rows that already had lat/lng
for idx, row in df[df['province'].isna()].iterrows():
    print(f"Reverse geocoding for index {idx}: lat={row['lat']}, lng={row['lng']}")
    province = reverse_geocode(row['lat'], row['lng'])
    df.at[idx, 'province'] = province
    print(f"Result - province: {province}")
    time.sleep(0.1)

# ✅ Keep only Ontario
df = df[df['province'] == "Ontario"]

# 🧮 Add user count (1 per user if not defined)
df['user_count'] = df.get('user_count', 1)

# 📍 Round to ~1km
df['lat_rounded'] = df['lat'].round(2)
df['lng_rounded'] = df['lng'].round(2)

# 🔢 Group by rounded location
grouped = df.groupby(['lat_rounded', 'lng_rounded'], as_index=False)['user_count'].sum()
grouped.rename(columns={'lat_rounded': 'lat', 'lng_rounded': 'lng'}, inplace=True)

# 🌎 Folium map with heat
m = folium.Map(location=[43.7, -79.4], zoom_start=8)
heat_data = grouped[['lat', 'lng', 'user_count']].values.tolist()
HeatMap(heat_data, radius=20, blur=15, max_zoom=13).add_to(m)

# 💾 Save
m.save("ontario_user_density_heatmap_folium_2.html")
print("✅ Final filtered Ontario-only heatmap saved")
