#missing cities
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

# Load the datasets
print("Loading datasets...")
arsenic_df = pd.read_csv("NATION-WIDE_arsenic_violations_(no-coords)ONLY STATES.csv")
uscities_df = pd.read_csv("uscities.csv")
print("Datasets loaded successfully.")

# Ensure consistent formatting
arsenic_df["City Name"] = arsenic_df["City Name"].str.title().str.strip()
arsenic_df["State"] = arsenic_df["State"].str.title().str.strip()
uscities_df["city"] = uscities_df["city"].str.title().str.strip()
uscities_df["state_name"] = uscities_df["state_name"].str.title().str.strip()

# Select relevant columns from uscities dataset
uscities_df = uscities_df[["city", "state_name", "lat", "lng"]]

# Merge datasets based on city and state
print("Merging datasets...")
merged_df = arsenic_df.merge(uscities_df, left_on=["City Name", "State"], right_on=["city", "state_name"], how="left")
print("Merge completed.")

# Drop redundant columns
merged_df = merged_df.drop(columns=["city", "state_name"])

# Function to fetch coordinates using Geopy
def get_coordinates(city, state):
    geolocator = Nominatim(user_agent="geo_locator")
    try:
        print(f"Fetching coordinates for: {city}, {state}")
        location = geolocator.geocode(f"{city}, {state}, USA", timeout=10)
        if location:
            print(f"Found: {location.latitude}, {location.longitude}")
            return location.latitude, location.longitude
    except GeocoderTimedOut:
        print(f"Timeout for {city}, {state}. Retrying...")
        time.sleep(1)
        return get_coordinates(city, state)  # Retry on timeout
    print(f"Coordinates not found for {city}, {state}")
    return None, None

# Fill missing lat/lng values
print("Checking for missing coordinates...")
for index, row in merged_df.iterrows():
    if pd.isnull(row["lat"]) or pd.isnull(row["lng"]):
        lat, lng = get_coordinates(row["City Name"], row["State"])
        merged_df.at[index, "lat"] = lat
        merged_df.at[index, "lng"] = lng

# Save the updated dataset
print("Saving updated dataset...")
merged_df.to_csv("updated_arsenic_violations_with_coords.csv", index=False)
print("Dataset saved as 'updated_arsenic_violations_with_coords.csv'.")
