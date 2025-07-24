import pandas as pd
import requests
import folium
from folium.plugins import HeatMap
import time

# 🔑 Replace with your actual Google Maps API key
GOOGLE_API_KEY = "AIzaSyCI6veWMOBWIIaxnn6sVNzRFwAyTJZO530"

# 📄 Load your dataset
df = pd.read_csv("Ontario_users.csv")

# 📍 Build address string for geocoding
df['full_address'] = df[['city', 'postal_code', 'state']].astype(str).agg(', '.join, axis=1)

# 🌐 Geocode missing lat/lng using Google Maps
def get_lat_lng_google(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": GOOGLE_API_KEY}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json().get("results")
            if results:
                location = results[0]["geometry"]["location"]
                return location["lat"], location["lng"]
    except:
        pass
    return None, None

# 🚧 Fill in missing coordinates
missing_coords = df['lat'].isna() | df['lng'].isna()
print(f"🔍 Geocoding {missing_coords.sum()} missing lat/lng rows...")

for idx, row in df[missing_coords].iterrows():
    lat, lng = get_lat_lng_google(row['full_address'])
    df.at[idx, 'lat'] = lat
    df.at[idx, 'lng'] = lng
    time.sleep(0.1)  # Avoid Google API rate limiting

# ❌ Drop rows still missing lat/lng
df.dropna(subset=['lat', 'lng'], inplace=True)

# 🧮 Assign count (if not provided)
df['user_count'] = df.get('user_count', 1)

# 📍 Round lat/lng to group nearby users (~1 km resolution)
df['lat_rounded'] = df['lat'].round(2)
df['lng_rounded'] = df['lng'].round(2)

# 📊 Aggregate user counts per rounded location
grouped = df.groupby(['lat_rounded', 'lng_rounded'], as_index=False)['user_count'].sum()
grouped.rename(columns={'lat_rounded': 'lat', 'lng_rounded': 'lng'}, inplace=True)

# 🗺️ Create Folium map
m = folium.Map(location=[43.7, -79.4], zoom_start=7)

# 🔥 Add density heatmap
heat_data = grouped[['lat', 'lng', 'user_count']].values.tolist()
HeatMap(heat_data, radius=20, blur=15, max_zoom=13).add_to(m)

# 💾 Save HTML
m.save("ontario_users_map_3_3.html")
print("✅ Heatmap saved to 'ontario_users_map_3_3.html'")
