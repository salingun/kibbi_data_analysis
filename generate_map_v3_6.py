import pandas as pd
import requests
import folium
from folium.plugins import HeatMap
import time

# 🔑 Replace with your actual key
GOOGLE_API_KEY = "AIzaSyCI6veWMOBWIIaxnn6sVNzRFwAyTJZO530"

# 📄 Load CSV file
df = pd.read_csv("Kibbi_users_2.csv")

# ✅ Build full address using street, postal_code, city, state
# address_fields = ['street', 'postal_code', 'city', 'state']
address_fields = ['city', 'postal_code', 'state']
df['full_address'] = df[address_fields].fillna('').astype(str).agg(', '.join, axis=1)

# ➕ Prepare geocoding result columns (non-destructive)
df['geo_lat'] = None
df['geo_lng'] = None
df['geo_city'] = None
df['geo_state'] = None
df['geo_country'] = None
df['geo_street'] = None
df['geo_postal_code'] = None

# # 🧭 Forward geocode (from address)
# def geocode_address(address, row=None):
#     # Try full address first
#     url = "https://maps.googleapis.com/maps/api/geocode/json"
#     params = {"address": address, "key": GOOGLE_API_KEY}
#     r = requests.get(url, params=params)
#     if r.status_code == 200:
#         res = r.json().get("results", [])
#         if res:
#             loc = res[0]["geometry"]["location"]
#             components = res[0]["address_components"]
#             formatted_address = res[0]["formatted_address"]
#             state = next((c["long_name"] for c in components if "administrative_area_level_1" in c["types"]), None)
#             city = next((c["long_name"] for c in components if "locality" in c["types"]), None)
#             country = next((c["long_name"] for c in components if "country" in c["types"]), None)
#             postal_code = next((c["long_name"] for c in components if "postal_code" in c["types"]), None)
#             street = next((c["long_name"] for c in components if "route" in c["types"]), None)
#             # If street, postal_code, city, state found, return
#             if street and postal_code and city and state:
#                 return loc["lat"], loc["lng"], city, state, country, street, postal_code
#     # Try postal_code, city, state
#     if row is not None:
#         addr2 = ', '.join([str(row.get('postal_code', '')), str(row.get('city', '')), str(row.get('state', ''))])
#         params = {"address": addr2, "key": GOOGLE_API_KEY}
#         r = requests.get(url, params=params)
#         if r.status_code == 200:
#             res = r.json().get("results", [])
#             if res:
#                 loc = res[0]["geometry"]["location"]
#                 components = res[0]["address_components"]
#                 formatted_address = res[0]["formatted_address"]
#                 state = next((c["long_name"] for c in components if "administrative_area_level_1" in c["types"]), None)
#                 city = next((c["long_name"] for c in components if "locality" in c["types"]), None)
#                 country = next((c["long_name"] for c in components if "country" in c["types"]), None)
#                 postal_code = next((c["long_name"] for c in components if "postal_code" in c["types"]), None)
#                 street = next((c["long_name"] for c in components if "route" in c["types"]), None)
#                 if postal_code and city and state:
#                     return loc["lat"], loc["lng"], city, state, country, street, postal_code
#         # Try city, state
#         addr3 = ', '.join([str(row.get('city', '')), str(row.get('state', ''))])
#         params = {"address": addr3, "key": GOOGLE_API_KEY}
#         r = requests.get(url, params=params)
#         if r.status_code == 200:
#             res = r.json().get("results", [])
#             if res:
#                 loc = res[0]["geometry"]["location"]
#                 components = res[0]["address_components"]
#                 formatted_address = res[0]["formatted_address"]
#                 state = next((c["long_name"] for c in components if "administrative_area_level_1" in c["types"]), None)
#                 city = next((c["long_name"] for c in components if "locality" in c["types"]), None)
#                 country = next((c["long_name"] for c in components if "country" in c["types"]), None)
#                 postal_code = next((c["long_name"] for c in components if "postal_code" in c["types"]), None)
#                 street = next((c["long_name"] for c in components if "route" in c["types"]), None)
#                 if city and state:
#                     return loc["lat"], loc["lng"], city, state, country, street, postal_code
#     # If all fail
#     return None, None, None, None, None, None, None


# 🧭 Forward geocode (from address)
def geocode_address(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": GOOGLE_API_KEY}
    r = requests.get(url, params=params)
    if r.status_code == 200:
        res = r.json().get("results", [])
        if res:
            loc = res[0]["geometry"]["location"]
            components = res[0]["address_components"]
            formatted_address = res[0]["formatted_address"]
            state = next((c["long_name"] for c in components if "administrative_area_level_1" in c["types"]), None)
            city = next((c["long_name"] for c in components if "locality" in c["types"]), None)
            country = next((c["long_name"] for c in components if "country" in c["types"]), None)
            postal_code = next((c["long_name"] for c in components if "postal_code" in c["types"]), None)
            return loc["lat"], loc["lng"], city, state, country, formatted_address, postal_code
    return None, None, None, None, None, None, None

# 🧭 Reverse geocode (from lat/lng)
def reverse_geocode(lat, lng):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"latlng": f"{lat},{lng}", "key": GOOGLE_API_KEY}
    r = requests.get(url, params=params)
    if r.status_code == 200:
        res = r.json().get("results", [])
        if res:
            components = res[0]["address_components"]
            formatted_address = res[0]["formatted_address"]
            state = next((c["long_name"] for c in components if "administrative_area_level_1" in c["types"]), None)
            city = next((c["long_name"] for c in components if "locality" in c["types"]), None)
            country = next((c["long_name"] for c in components if "country" in c["types"]), None)
            postal_code = next((c["long_name"] for c in components if "postal_code" in c["types"]), None)
            return city, state, country, formatted_address, postal_code
    return None, None, None, None, None

# 🔍 Forward geocode rows missing lat/lng
missing_coords = df['lat'].isna() | df['lng'].isna()
for idx, row in df[missing_coords].iterrows():
    print(f"Geocoding index {idx}: {row['full_address']}")
    geo_lat, geo_lng, geo_city, geo_state, geo_country, geo_street, geo_postal_code = geocode_address(row['full_address'])
    df.at[idx, 'geo_lat'] = geo_lat
    df.at[idx, 'geo_lng'] = geo_lng
    df.at[idx, 'geo_city'] = geo_city
    df.at[idx, 'geo_state'] = geo_state
    df.at[idx, 'geo_country'] = geo_country
    df.at[idx, 'geo_street'] = geo_street
    df.at[idx, 'geo_postal_code'] = geo_postal_code
    print(f"→ geo_lat: {geo_lat}, geo_lng: {geo_lng}, geo_city: {geo_city}, geo_state: {geo_state}, geo_country: {geo_country}, geo_postal_code: {geo_postal_code}")
    time.sleep(0.1)

# 🔍 Reverse geocode rows with lat/lng but missing geo_* fields
missing_geo_fields = (
    df['lat'].notna() &
    df['lng'].notna() &
    (
        df['geo_lat'].isna() |
        df['geo_lng'].isna() |
        df['geo_city'].isna() |
        df['geo_state'].isna() |
        df['geo_country'].isna()
    )
)

for idx, row in df[missing_geo_fields].iterrows():
    print(f"Reverse geocoding index {idx}: lat={row['lat']}, lng={row['lng']}")
    geo_city, geo_state, geo_country, geo_street, geo_postal_code = reverse_geocode(row['lat'], row['lng'])
    df.at[idx, 'geo_lat'] = row['lat']
    df.at[idx, 'geo_lng'] = row['lng']
    df.at[idx, 'geo_city'] = geo_city
    df.at[idx, 'geo_state'] = geo_state
    df.at[idx, 'geo_country'] = geo_country
    df.at[idx, 'geo_street'] = geo_street
    df.at[idx, 'geo_postal_code'] = geo_postal_code
    print(f"→ geo_city: {geo_city}, geo_state: {geo_state}, geo_country: {geo_country}, geo_postal_code: {geo_postal_code}")
    time.sleep(0.1)

# 💾 Save full dataset before filtering
df.to_csv("Kibbi_users_geocoded_full_dataset.csv", index=False)
print("✅ Full dataset saved: Kibbi_users_geocoded_full_dataset.csv")

# ✅ Filter: Keep only users in Canada
df = df[df['geo_country'] == "Canada"]
print(f"📊 Filtered dataset size: {len(df)} rows")

# 🧮 Add default user count if missing
if 'user_count' not in df.columns:
    df['user_count'] = 1

# 📍 Round coordinates for grouping (approx 1km)
df['lat_rounded'] = df['geo_lat'].astype(float).round(2)
df['lng_rounded'] = df['geo_lng'].astype(float).round(2)

# 🔢 Group nearby points
grouped = df.groupby(['lat_rounded', 'lng_rounded'], as_index=False)['user_count'].sum()
grouped.rename(columns={'lat_rounded': 'lat', 'lng_rounded': 'lng'}, inplace=True)

# 🌎 Draw heatmap
m = folium.Map(location=[56.1304, -106.3468], zoom_start=4)  # Center of Canada
heat_data = grouped[['lat', 'lng', 'user_count']].values.tolist()
HeatMap(heat_data, radius=20, blur=15, max_zoom=13).add_to(m)

# 💾 Save heatmap to HTML
m.save("canada_user_density_heatmap.html")
print("✅ Final heatmap saved: canada_user_density_heatmap.html")
