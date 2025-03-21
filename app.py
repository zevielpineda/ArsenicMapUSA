import pandas as pd
import folium
from folium.plugins import MarkerCluster
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import os
import math

# Load dataset
file_path = os.path.join(os.path.dirname(__file__), "formatted_completely_filled_lat_lng_violations.csv")
df = pd.read_csv(file_path)

# ✅ Remove commas before converting to numeric
df['population'] = df['population'].astype(str).str.replace(',', '')  # Remove commas
df['population'] = pd.to_numeric(df['population'], errors='coerce')  # Convert to integer

# Convert compliance period begin date to year
df['year'] = pd.to_datetime(df['compliance period begin date'], errors='coerce').dt.year

# Function to create the map
def create_map(selected_year):
    filtered_df = df[df['year'] == selected_year].dropna(subset=['lat', 'lng'])

    if filtered_df.empty:
        print(f"⚠️ No data for {selected_year}. Creating an empty map.")
        m = folium.Map(location=[37.0902, -95.7129], zoom_start=5)
    else:
        grouped = filtered_df.groupby(['lat', 'lng', 'pws id']).agg({
            'population': 'max',
            'pws name': 'first',
            'State': 'first',
            'City Name': 'first'
        }).reset_index()

        final_grouped = grouped.groupby(['lat', 'lng']).agg({
            'population': 'sum',
            'pws id': list,
            'pws name': list,
            'State': 'first',
            'City Name': 'first'
        }).reset_index()

        max_violations = final_grouped['pws id'].apply(len).max() if not final_grouped.empty else 1

        m = folium.Map(location=[filtered_df['lat'].mean(), filtered_df['lng'].mean()], zoom_start=5)
        marker_cluster = MarkerCluster().add_to(m)

        for _, row in final_grouped.iterrows():
            num_violations = len(row['pws id']) if isinstance(row['pws id'], list) else 1
            color_intensity = int((num_violations / max_violations) * 255) if max_violations else 50
            color = f'#{255-color_intensity:02x}{100-color_intensity//2:02x}00'

            radius = max(5, math.log1p(row['population']) * 2) if row['population'] >= 1000 else 5  # Adjusted radius calculation

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
                radius=radius,  # Adjusted circle size
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_text, max_width=300)
            ).add_to(marker_cluster)

    map_file = "arsenic_map.html"
    m.save(map_file)
    return map_file

# Dash app and Google Tag
dash_app = dash.Dash(
    __name__,
    index_string="""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">  <!-- ✅ Ensures proper scaling -->
    <title>Arsenic Violations Map</title>

    <!-- Google Tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-HZX5K597S0"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-HZX5K597S0');
    </script>

    <style>
        body {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            margin: 0;
            padding-bottom: 34px;
        }
        #app-content {
            flex: 1;
        }
        footer {
            position: relative;
            width: 100%;
            background-color: transparent;
            text-align: center;
            padding: 10px;
            font-size: 14px;
            color: gray;
            box-shadow: none;
        }
    </style>
</head>
<body>
    <div id="app-content">
        {%app_entry%}
    </div>
    <footer>
        Created by Zeviel Pineda © 2025 | Adapted from EPA Database
    </footer>
    <footer>{%config%} {%scripts%} {%renderer%}</footer>
</body>
</html>
"""
)

dash_app.config.suppress_callback_exceptions = True

# Create initial map file
initial_map_file = create_map(2001)

# App layout with sticky slider and total population affected
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

    html.Div(style={"height": "120px"}),

    html.Div([
        html.Span("Total Population Affected: ", style={"fontWeight": "bold", "fontSize": "20px"}),
        html.Span(id="total-population", style={"color": "red", "fontSize": "20px", "fontWeight": "bold"})
    ], style={"textAlign": "center", "margin": "20px"}),

    html.Div([
        html.Iframe(
            id='map', 
            srcDoc=open(initial_map_file, "r", encoding="utf-8").read(), 
            width='100%', 
            height='600'
        )
    ])
])

# Callback to update map and total population
@dash_app.callback(
    [Output('map', 'srcDoc'), Output('total-population', 'children')],
    [Input('year-slider', 'value')]
)
def update_map(selected_year):
    print(f"🔄 Updating map for year: {selected_year}")
    try:
        selected_year = int(selected_year)
        map_file = create_map(selected_year)

        # Calculate total affected population
        total_population = df[df['year'] == selected_year]['population'].sum()
        total_population_text = f"{total_population:,.0f}"  # Format with commas

        if not os.path.exists(map_file):
            print(f"❌ Error: {map_file} not found.")
            return dash.no_update, dash.no_update
        
        with open(map_file, "r", encoding="utf-8") as f:
            return f.read(), total_population_text
    
    except Exception as e:
        print(f"❌ Error in update_map: {e}")
        return dash.no_update, dash.no_update  # Prevents breaking layout


if __name__ == '__main__':
    dash_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=True)

server = dash_app.server
