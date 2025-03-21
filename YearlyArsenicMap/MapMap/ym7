import pandas as pd
import folium
from folium.plugins import MarkerCluster
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import os

# Load dataset
file_path = "c:/Users/cdpin/OneDrive/Documents/National Arsenic Stuff for VSC/YearlyArsenicMap/MapMap/formatted_completely_filled_lat_lng_violations.csv"
df = pd.read_csv(file_path)

# ✅ Remove commas before converting to numeric
df['population'] = df['population'].astype(str).str.replace(',', '')  # Remove commas
df['population'] = pd.to_numeric(df['population'], errors='coerce')  # Convert to integer

# Convert compliance period begin date to year
df['year'] = pd.to_datetime(df['compliance period begin date'], errors='coerce').dt.year

# Function to create the map
def create_map(selected_year):
    filtered_df = df[df['year'] == selected_year]

    if filtered_df.empty:
        print(f"⚠️ No data for {selected_year}. Creating an empty map.")
        m = folium.Map(location=[37.0902, -95.7129], zoom_start=5)
    else:
        # ✅ FIX: Group by lat, lng, and PWS ID, summing populations per PWS ID
        grouped = filtered_df.groupby(['lat', 'lng', 'pws id']).agg({
            'population': 'max',  # Take the max per PWS ID
            'pws name': 'first',
            'State': 'first',
            'City Name': 'first'
        }).reset_index()

        # ✅ Sum population across all PWS IDs at the same lat/lng
        final_grouped = grouped.groupby(['lat', 'lng']).agg({
            'population': 'sum',  # Sum populations of all PWS IDs at this location
            'pws id': list,
            'pws name': list,
            'State': 'first',
            'City Name': 'first'
        }).reset_index()

        max_violations = final_grouped['pws id'].apply(len).max() if not final_grouped.empty else 1

        m = folium.Map(location=[filtered_df['lat'].mean(), filtered_df['lng'].mean()], zoom_start=5)
        marker_cluster = MarkerCluster().add_to(m)

        for _, row in final_grouped.iterrows():
            num_violations = len(row['pws id'])
            color_intensity = int((num_violations / max_violations) * 255) if max_violations else 50
            color = f'#{255-color_intensity:02x}{100-color_intensity//2:02x}00'

            popup_text = f"""
            <b>State:</b> {row['State']}<br>
            <b>City:</b> {row['City Name']}<br>
            <b>PWS IDs:</b> {', '.join(row['pws id'])}<br>
            <b>PWS Names:</b> {', '.join(row['pws name'])}<br>
            <b>Violations:</b> {num_violations}<br>
            <b>Total Population Affected:</b> {row['population']}
            """

            folium.CircleMarker(
                location=[row['lat'], row['lng']],
                radius=max(5, row['population'] / 5000),  # ✅ Adjusted scaling factor
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_text, max_width=300)
            ).add_to(marker_cluster)

    # Save map
    map_file = "arsenic_map.html"
    m.save(map_file)
    return map_file

# Dash app
dash_app = dash.Dash(__name__)
dash_app.config.suppress_callback_exceptions = True

# Create initial map file
initial_map_file = create_map(2001)

# App layout with sticky slider
dash_app.layout = html.Div([
    html.Div([
        html.H1("Arsenic Violations Map", style={"textAlign": "center"}),
        dcc.Slider(
            id='year-slider',
            min=2001,
            max=2024,
            value=2001,
            marks={i: str(i) for i in range(2001, 2025)},
            step=1
        )
    ], style={
        "position": "fixed",
        "top": "0",
        "left": "0",
        "width": "100%",
        "backgroundColor": "white",
        "zIndex": "1000",
        "padding": "10px",
        "boxShadow": "0px 2px 5px rgba(0,0,0,0.2)"
    }),

    html.Div(style={"height": "100px"}),  # Spacer

    html.Div([
        html.Iframe(
            id='map', 
            srcDoc=open(initial_map_file, "r", encoding="utf-8").read(), 
            width='100%', 
            height='600'
        )
    ])
])

# Callback to update map
@dash_app.callback(
    Output('map', 'srcDoc'),
    [Input('year-slider', 'value')]
)
def update_map(selected_year):
    print(f"🔄 Updating map for year: {selected_year}")

    try:
        selected_year = int(selected_year)
        map_file = create_map(selected_year)

        if not os.path.exists(map_file):
            print(f"❌ Error: {map_file} not found.")
            return dash.no_update

        with open(map_file, "r", encoding="utf-8") as f:
            return f.read()

    except Exception as e:
        print(f"❌ Error in update_map: {e}")
        return dash.no_update  # Prevents breaking layout

if __name__ == '__main__':
    dash_app.run(debug=True)
