import pandas as pd

# Load the datasets
arsenic_df = pd.read_csv("NATION-WIDE_arsenic_violations_(no-coords)ONLY STATES.csv")
uscities_df = pd.read_csv("uscities.csv")

# Ensure consistent formatting
arsenic_df["City Name"] = arsenic_df["City Name"].str.title().str.strip()
arsenic_df["State"] = arsenic_df["State"].str.title().str.strip()
uscities_df["city"] = uscities_df["city"].str.title().str.strip()
uscities_df["state_name"] = uscities_df["state_name"].str.title().str.strip()

# Select relevant columns from uscities dataset
uscities_df = uscities_df[["city", "state_name", "lat", "lng"]]

# Merge datasets based on city and state
merged_df = arsenic_df.merge(uscities_df, left_on=["City Name", "State"], right_on=["city", "state_name"], how="left")

# Drop redundant columns
merged_df = merged_df.drop(columns=["city", "state_name"])

# Save the updated dataset
merged_df.to_csv("updated_arsenic_violations_with_coords.csv", index=False)

print("Dataset updated with latitude and longitude saved as 'updated_arsenic_violations_with_coords.csv'")
