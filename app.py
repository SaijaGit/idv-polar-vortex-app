from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from pathlib import Path
from plotly.subplots import make_subplots
from functools import lru_cache

from dash import Dash, dcc, html, Input, Output

# =====================================================
# 1. LADATAAN DATA
# =====================================================

vortex_path = Path("data_processed/vortex/vortex_all.csv")
temp_folder = Path("data_processed/temp_clean")

@lru_cache(maxsize=2)
def load_mean_temps(grid_resolution):
    path = temp_folder / f"mean_temps_{grid_resolution}.csv"
    return pd.read_csv(path)

@lru_cache(maxsize=20)
def load_temp_year(year, grid_resolution):
    path = temp_folder / f"temp_{year}_{grid_resolution}.csv"
    return pd.read_csv(path, parse_dates=["date"])

df_vortex = pd.read_csv(vortex_path, parse_dates=["date"], low_memory=False)

# Poistetaan karkauspäivät ennen fake-päivämäärän luomista
df_vortex = df_vortex[
    ~((df_vortex["date"].dt.month == 2) & (df_vortex["date"].dt.day == 29))
]

# Talvikausi: marraskuu–maaliskuu
df_vortex["winter"] = df_vortex["date"].apply(
    lambda d: f"{d.year}-{d.year+1}" if d.month >= 11 else f"{d.year-1}-{d.year}"
)

# Poistetaan epätäydelliset talvet
df_vortex = df_vortex[
    ~df_vortex["winter"].isin(["1974-1975", "2025-2026"])
]

df_vortex["winter_day"] = df_vortex["date"].apply(
    lambda d: (d - pd.Timestamp(f"{d.year if d.month >= 11 else d.year-1}-11-01")).days
)

df_vortex["winter_date"] = df_vortex["date"].apply(
    lambda d: d.replace(year=2001 if d.month >= 11 else 2002)
)

default_date = "2025-01-01"



all_winters = sorted(
    df_vortex["winter"].dropna().unique(),
    reverse=True
)

palette = pc.sample_colorscale(
    "Rainbow",
    [i / (len(all_winters) - 1) for i in range(len(all_winters))]
)

winter_color_map = {
    winter: palette[i]
    for i, winter in enumerate(all_winters)
}

# =====================================================
# 2. APP
# =====================================================



app = Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H2("Polar vortex strength and temperatures during winter seasons 1975 - 2025"),

    html.Label("Select winters"),
    dcc.Dropdown(
        id="winter-select",
        options=[
            {"label": w, "value": w}
            for w in all_winters
        ],
        value=["2024-2025"],
        multi=True
    ),

    html.Br(),

    html.Label("Comparison mode"),
    dcc.RadioItems(
        id="comparison-mode",
        options=[
            {"label": "Overlay", "value": "overlay"},
            {"label": "Separate", "value": "separate"}
        ],
        value="overlay",
        inline=True
    ),

    html.Br(),

    html.Label("Map variable"),
    dcc.RadioItems(
        id="map-variable",
        options=[
            {"label": "Temperature", "value": "temp_c"},
            {"label": "Temperature anomaly", "value": "temp_anomaly"}
        ],
        value="temp_c",
        inline=True
    ),

    html.Br(),

    html.Label("Grid resolution"),
    dcc.RadioItems(
        id="grid-resolution",
        options=[
            {"label": "5° (faster)", "value": "5deg"},
            {"label": "2.5° (detailed)", "value": "2p5deg"},
        ],
        value="5deg",   # oletus nopeampi
        inline=True
    ),

    html.Br(),

    html.Div(id="selected-date-text"),

    dcc.Store(id="selected-date-store", data=default_date),

    html.Div(
        dcc.Graph(
            id="vortex-graph",
            style={"width": "100%"},
            config={"responsive": True}
        ),
        style={
            "overflowX": "auto",
            "overflowY": "hidden",
            "width": "100%",
        }
    ),

    dcc.Graph(id="map-graph")
])


# =====================================================
# 3. CALLBACK: VORTEX-KUVAAJA
# =====================================================


@app.callback(
    Output("vortex-graph", "figure"),
    Input("winter-select", "value"),
    Input("comparison-mode", "value"),
    Input("selected-date-store", "data")
)
def update_vortex_graph(selected_winters, mode, selected_date):
    if not selected_winters:
        selected_winters = ["2024-2025"]

    selected_winters = sorted(selected_winters)

    filtered = df_vortex[df_vortex["winter"].isin(selected_winters)].copy()
    filtered["date_str"] = filtered["date"].dt.strftime("%Y-%m-%d")

    y_min = df_vortex["vortex_strength"].min()
    y_max = df_vortex["vortex_strength"].max()

    if mode == "separate":
        n = len(selected_winters)

        subplot_width = 230
        min_width = 1400
        graph_width = max(min_width, subplot_width * n)

        gap_px = 6
        horizontal_spacing = gap_px / graph_width

        fig = make_subplots(
            rows=1,
            cols=n,
            shared_yaxes=True,
            subplot_titles=selected_winters,
            horizontal_spacing=horizontal_spacing
        )

        for i, winter in enumerate(selected_winters, start=1):
            df_winter = filtered[filtered["winter"] == winter]

            fig.add_trace(
                go.Scatter(
                    x=df_winter["winter_date"],
                    y=df_winter["vortex_strength"],
                    mode="lines",
                    line=dict(color=winter_color_map[winter]),
                    customdata=df_winter[["date_str"]],
                    showlegend=False
                ),
                row=1,
                col=i
            )

            fig.update_xaxes(
                tickformat="%b %d",
                dtick="M1",
                tickangle=90,
                row=1,
                col=i
            )

            fig.update_yaxes(range=[y_min, y_max], row=1, col=i)

            if i > 1:
                fig.update_yaxes(showticklabels=False, row=1, col=i)

        fig.update_yaxes(title_text="Vortex strength", row=1, col=1)

        fig.update_layout(
            title="Polar vortex strength (zonal wind speed)",
            width=graph_width,
            height=350,
            hovermode="closest",
            clickmode="event+select",
            margin=dict(l=60, r=30, t=70, b=90)
        )

    else:
        if len(selected_winters) <= 1:
            title = f"Polar vortex strength (zonal wind speed) on winter {selected_winters[0]}"
        else:
            title = "Polar vortex strength (zonal wind speed) comparison"

        fig = px.line(
            filtered,
            x="winter_date",
            y="vortex_strength",
            color="winter",
            title=title,
            labels={
                "winter_date": "Date in winter season",
                "vortex_strength": "Vortex strength (m/s)"
            },
            custom_data=["date_str"],
            color_discrete_map=winter_color_map,
        )

        fig.update_yaxes(range=[y_min, y_max])

    selected_ts = pd.Timestamp(selected_date)
    selected_row = filtered[filtered["date"] == selected_ts]

    if not selected_row.empty:
        selected_winter = selected_row["winter"].iloc[0]

        if mode == "separate":
            selected_col = selected_winters.index(selected_winter) + 1

            fig.add_trace(
                go.Scatter(
                    x=selected_row["winter_date"],
                    y=selected_row["vortex_strength"],
                    mode="markers",
                    marker=dict(color="red", size=12),
                    name="Selected date",
                    showlegend=True,
                    customdata=selected_row[["date_str"]],
                ),
                row=1,
                col=selected_col
            )

        else:
            fig.add_trace(
                go.Scatter(
                    x=selected_row["winter_date"],
                    y=selected_row["vortex_strength"],
                    mode="markers",
                    marker=dict(color="red", size=12),
                    name="Selected date",
                    customdata=selected_row[["date_str"]],
                )
        )

    if mode == "separate":
        subplot_width = 230
        min_width = 1400
        graph_width = max(min_width, subplot_width * len(selected_winters))
    else:
        graph_width = None

    fig.update_layout(
        width=graph_width,
        autosize=(mode == "overlay"),
        height=350,
        hovermode="closest",
        clickmode="event+select"
    )

    fig.update_xaxes(
        tickformat="%b %d",   # Nov 01, Dec 15 jne
    )

    fig.update_xaxes(
        dtick="M1"
    )
    

    return fig


# =====================================================
# 4. CALLBACK: KLIKKAUS VORTEX-KUVAAJASTA
# =====================================================

@app.callback(
    Output("selected-date-store", "data"),
    Input("vortex-graph", "clickData"),
    prevent_initial_call=True
)
def store_selected_date(clickData):
    if clickData is None:
        return default_date

    return clickData["points"][0]["customdata"][0]


# =====================================================
# 5. CALLBACK: KARTTA
# =====================================================

@app.callback(
    Output("map-graph", "figure"),
    Output("selected-date-text", "children"),
    Input("selected-date-store", "data"),
    Input("map-variable", "value"),
    Input("grid-resolution", "value"),
)
def update_map(selected_date, map_variable, grid_resolution):

    selected_ts = pd.Timestamp(selected_date)
    year = selected_ts.year

    file_path = temp_folder / f"temp_{year}_{grid_resolution}.csv"

    if not file_path.exists():
        fig = go.Figure()
        fig.update_layout(title=f"No data for {year}")
        return fig, f"Selected date: {selected_date}"

    df_temp_year = pd.read_csv(file_path, parse_dates=["date"])

    df_day = df_temp_year[df_temp_year["date"] == selected_ts].copy()

    if df_day.empty:
        fig = go.Figure()
        fig.update_layout(title=f"No data for {selected_date}")
        return fig, f"Selected date: {selected_date}"
    
    df_day["dayofyear"] = df_day["date"].dt.dayofyear

    df_clim = load_mean_temps(grid_resolution)

    df_day = df_day.merge(
        df_clim,
        on=["latitude", "longitude", "dayofyear"],
        how="left"
    )

    df_day["temp_anomaly"] = df_day["temp_c"] - df_day["mean_temp_c"]

    title_variable = (
        "Temperature anomaly"
        if map_variable == "temp_anomaly"
        else "Temperature"
    )
    vortex_row = df_vortex[df_vortex["date"] == selected_ts]

    if not vortex_row.empty:
        vortex_strength = vortex_row["vortex_strength"].iloc[0]
        title = f"{title_variable} on {selected_date} | Vortex strength: {vortex_strength:.1f} m/s"
    else:
        title = f"{title_variable} on {selected_date}"

    if map_variable == "temp_c":
        color_range = [-50, 35]      # absolute temperature in °C

    else:
        color_range = [-20, 20]      # anomaly in °C

    fig = px.scatter_geo(
        df_day,
        lat="latitude",
        lon="longitude",
        color=map_variable,
        color_continuous_scale="RdBu_r",
        range_color=color_range,
        projection="natural earth",
        title=title,
    )

    marker_size = 14 if grid_resolution == "5deg" else 7

    fig.update_traces(marker=dict(size=marker_size, opacity=0.9))

    fig.update_geos(
        showcoastlines=True,
        coastlinecolor="gray",
        showland=True,
        landcolor="rgb(240,240,240)",
        showocean=True,
        oceancolor="rgb(230,240,255)",
        lataxis_range=[25, 90],
    )

    
    fig.update_layout(
        height=500,
        margin=dict(l=40, r=80, t=60, b=20),
        coloraxis_colorbar=dict(
            title="°C",
            len=0.75,
            y=0.5
        )
    )

    return fig, f"Selected date: {selected_date}"


# =====================================================
# 6. KÄYNNISTYS
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)
