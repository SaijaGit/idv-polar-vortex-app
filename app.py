########################################################################
# ABOUT THIS FILE
#########################################################################
#
# This is the main Dash app for the Interactive Data Visualizations 2026 course project.
# The data is already loaded and processed before this stage, so this file mainly builds the UI, loads the csv files and connects
# the interactions between the vortex curve and the map.
#
#########################################################################


from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from pathlib import Path
from plotly.subplots import make_subplots
from functools import lru_cache
import dash_bootstrap_components as dbc
import dash
from dash import Dash, dcc, html, Input, Output

##########################################################################
# LOAD DATA
##########################################################################
#
# The vortex data is loaded immediately because it is quite small.
# The temperature data is still large, so it is loaded later only for the selected year and grid resolution.
#
#
vortex_path = Path("data_processed/vortex/vortex_all.csv")

temp_path = Path("data_processed/temp_clean")

ssw_path = Path("data_processed/ssw_events/ssw_events.csv")


@lru_cache(maxsize=2)
def load_climatology(grid_resolution):
    path = temp_path / f"mean_temps_{grid_resolution}.csv"
    return pd.read_csv(path)

df_vortex = pd.read_csv(vortex_path, parse_dates=["date"], low_memory=False)


##########################################################################
# PREPARE THE WINTER TIMELINE
##########################################################################

# Removing leap days before creating a fake date
df_vortex = df_vortex[
    ~((df_vortex["date"].dt.month == 2) & (df_vortex["date"].dt.day == 29))
]

# Winter season: November–March
df_vortex["winter"] = df_vortex["date"].apply(
    lambda d: f"{d.year}-{d.year+1}" if d.month >= 11 else f"{d.year-1}-{d.year}"
)

# Removing first and last incomplete winters
df_vortex = df_vortex[
    ~df_vortex["winter"].isin(["1974-1975", "2025-2026"])
]

# Number of days from the start of the winter season.
df_vortex["winter_day"] = df_vortex["date"].apply(
    lambda d: (d - pd.Timestamp(f"{d.year if d.month >= 11 else d.year-1}-11-01")).days
)

df_vortex["winter_date"] = df_vortex["date"].apply(
    lambda d: d.replace(year=2001 if d.month >= 11 else 2002)
)

default_date = "2025-01-01"


# ###########################################################################
# COLORS FOR WINTERS
# ###########################################################################
#
# Each winter season gets its own color. The same color is used every time that winter is drawn.
#
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

# ###########################################################################
# LOAD OFFICIAL SSW EVENTS
# ###########################################################################
#
# The official SSW dates are loaded from csv file. 
# They are handled in the same winter season format as the vortex data, so they can be shown on the curve and
# selected from the dropdown menu.
#

df_ssw = pd.read_csv(ssw_path, parse_dates=["date"])

df_ssw = df_ssw[
    ~((df_ssw["date"].dt.month == 2) & (df_ssw["date"].dt.day == 29))
]

df_ssw["winter"] = df_ssw["date"].apply(
    lambda d: f"{d.year}-{d.year+1}" if d.month >= 11 else f"{d.year-1}-{d.year}"
)

df_ssw["winter_date"] = df_ssw["date"].apply(
    lambda d: d.replace(year=2001 if d.month >= 11 else 2002)
)

###########################################################################
#  CREATE THE DASH APP
###########################################################################
#
# The app uses Dash Bootstrap Components for the layout, cards and tooltips. 
# And theme.
#
# The actual visualizations are Plotly graphs.
# 

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="Polar vortex and winter temperatures"
)

server = app.server

info_icon_style = {
    "cursor": "pointer",
    "color": "#0d6efd",
    "marginLeft": "5px",
    "fontWeight": "bold"
}

###########################################################################
#  APP LAYOUT
###########################################################################
# The layout has two main parts. 
# The left side contains the controls and info boxes, 
# and the right side contains the selected date indicator, vortex curve and temperature map.
#

app.layout = dbc.Container(
    [

        dbc.Row(
            [
                dbc.Col(
                    html.H2(
                        "Polar vortex strength and temperatures during winter seasons 1975–2025",
                        className="my-3"
                    ),
                    width=12
                )
            ]
        ),

        dbc.Row(
            [
                                                            
                # ###########################################################################
                # LEFT: CONTROLS
                # ###########################################################################
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                dbc.Accordion(
                                    [
                                        dbc.AccordionItem(
                                            [
                                                html.P(
                                                    "The Arctic polar vortex is a circulation of westerly winds in the stratosphere around the North Pole. It's strength is measured by the mean wind speed near latitude 60° N."
                                                ),
                                                html.P(
                                                    "Polar vortex exists only on winter. When it is strong, it encloses a large pool of extremely cold air on the arctic region. When the vortex weakens, cold air can spread southward. "
                                                ),

                                                html.P(
                                                    "A sudden stratospheric warming (SSW) event occurs when the Arctic polar vortex weakens rapidly and temperatures in the polar stratosphere rise sharply. This is often associated with unusually cold winter weather in the mid-latitudes during the following weeks."
                                                ),
                                                html.P(
                                                    "This visualization lets you examine the polar vortex strength with temperatures on the the nortern latitudes during winter seasons 1975 - 2025."
                                                ),
                                                html.A(
                                                    "NOAA: Understanding the Arctic polar vortex",
                                                    href="https://www.climate.gov/news-features/understanding-climate/understanding-arctic-polar-vortex",
                                                    target="_blank"
                                                ),

                                            ],
                                            title="What is the polar vortex?"
                                        )
                                    ],
                                    start_collapsed=True,
                                    className="mb-3"
                                ),

                                #html.H5("Controls", className="card-title"),
                                #html.B("Controls "),
                                #html.Br(),

                                html.Label("Select winters"),
                                dcc.Dropdown(
                                    id="winter-select",
                                    options=[
                                        {"label": w, "value": w}
                                        for w in all_winters
                                    ],
                                    value=["2024-2025"],
                                    multi=True,
                                    maxHeight=400
                                ),

                                html.Br(),

                                html.Label(
                                    [
                                        "Vortex curve display mode",
                                        html.Span("ⓘ", id="comparison-info", style=info_icon_style)
                                    ]
                                ),
                                dbc.Tooltip(
                                    "Overlay is useful for comparing winters on the same seasonal timeline. \n"
                                    "Separate view is useful when you want to eaxamine polar vortex trends over many consecutive winters.",
                                    target="comparison-info",
                                    placement="right",
                                ),

                                dcc.RadioItems(
                                    id="comparison-mode",
                                    options=[
                                        {"label": "Overlay", "value": "overlay"},
                                        {"label": "Side-by-side", "value": "separate"}
                                    ],
                                    value="overlay",
                                    inline=False
                                ),

                                html.Br(),

                                html.Label(
                                    [
                                        "Temperature map mode",
                                        html.Span("ⓘ", id="temp-info", style=info_icon_style)
                                    ]
                                ),
                                dbc.Tooltip(
                                    "Temperature shows the actual measured temperature. \n"
                                    "Temperature anomaly shows how much warmer or colder the day is "
                                    "compared with the long-term average for the same calendar date.",
                                    target="temp-info",
                                    placement="right",
                                ),

                                dcc.RadioItems(
                                    id="map-variable",
                                    options=[
                                        {"label": "Temperature", "value": "temp_c"},
                                        {"label": "Temperature anomaly", "value": "temp_anomaly"}
                                    ],
                                    value="temp_c",
                                    inline=False
                                ),

                                html.Br(),

                                html.Label(
                                    [
                                        "Map grid resolution",
                                        html.Span("ⓘ", id="grid-info", style=info_icon_style)
                                    ]
                                ),
                                dbc.Tooltip(
                                    "5° is faster and smoother to use. \n2.5° shows more detail but may load slower.",
                                    target="grid-info",
                                    placement="right",
                                ),

                                dcc.RadioItems(
                                    id="grid-resolution",
                                    options=[
                                        {"label": "5° faster", "value": "5deg"},
                                        {"label": "2.5° detailed", "value": "2p5deg"},
                                    ],
                                    value="5deg",
                                    inline=False
                                ),

                                html.Hr(),

                                html.Div(
                                    [   
                                        html.B("SSW events "),
                                        html.Span("ⓘ", id="ssw-info", style=info_icon_style),
                                        html.Br(),
                                        "Blue circles ",
                                        html.Span(
                                            "●",
                                            style={
                                                "color": "blue",
                                                "fontSize": "1.2rem",
                                                "marginRight": "4px"
                                            }
                                        ),
                                        "on the vortex curve mark official major sudden stratospheric warming events.",
                                    ],
                                    style={"fontSize": "1rem", "marginTop": "4px"}
                                ),

                                dbc.Tooltip(
                                    "Use the dropdown menu to jump directly to official SSW event dates. Labels such as ERA5 indicate the dataset used by the NOAA CSL SSW Compendium to identify the event.",
                                    target="ssw-info",
                                    placement="right",
                                ),

                                html.Br(),

                                html.Label("Find official SSW event"),
                                dcc.Dropdown(
                                    id="ssw-event-select",
                                    options=[
                                        {
                                            "label": f"{row['date'].strftime('%Y-%m-%d')}",
                                            "value": row["date"].strftime("%Y-%m-%d")
                                        }
                                        for _, row in df_ssw.sort_values("date", ascending=False).iterrows()
                                        if row["winter"] in all_winters
                                    ],
                                    placeholder="Select event date",
                                    clearable=True,
                                    maxHeight=400
                                ),

                                html.Hr(),

                                dbc.Accordion(
                                    [
                                        dbc.AccordionItem(
                                            [

                                                html.P(
                                                    [
                                                        html.B("Temperature data: "),
                                                        html.Br(),
                                                        html.A(
                                                            "ERA5 hourly data on single levels from 1940 to present",
                                                            href="https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview",
                                                            target="_blank"
                                                        ),
                                                        html.Br(),
                                                        "DOI: 10.24381/cds.adbb2d47"
                                                    ] ),
                                                
                                                html.P(
                                                    [
                                                        html.B("Wind speed data for calculating polar vortex strength: "),
                                                        html.Br(),
                                                        html.A(
                                                            "ERA5 hourly data on pressure levels from 1940 to present",
                                                            href="https://cds.climate.copernicus.eu/datasets/reanalysis-era5-pressure-levels?tab=overview",
                                                            target="_blank"
                                                        ),
                                                        html.Br(),
                                                        "DOI: 10.24381/cds.bd0915c6"
                                                    ] ),
                                                
                                                html.P(
                                                    [
                                                        "ERA5 reanalysis datasets are from the Copernicus Climate Change Service:",
                                                        html.Br(),
                                                        html.A(
                                                            "Climate Data Store (CDS)",
                                                            href="https://cds.climate.copernicus.eu/",
                                                            target="_blank"
                                                        ),
                                                    ] ),

                                                html.P(
                                                    [
                                                        html.B("Official SSW events: "),
                                                        html.Br(),
                                                        html.A(
                                                            "Sudden Stratospheric Warming Compendium data set",
                                                            href="https://csl.noaa.gov/groups/csl8/sswcompendium/majorevents.html",
                                                            target="_blank"
                                                        ),
                                                    ]
                                                ),

                                            ],
                                            title="Data sources"
                                        )
                                    ],
                                    start_collapsed=True,
                                    className="mt-3"
                                ),

                            ]
                        ),
                        className="shadow-sm"
                    ),
                    xs=12,
                    md=3,
                    style={
                        "position": "sticky",
                        "top": "10px",
                        "alignSelf": "flex-start",
                        "height": "fit-content",
                        "zIndex": 10
                    }
                ),

                # ###########################################################################
                # RIGHT: VISUALIZATION
                # ###########################################################################
                dbc.Col(
                    [

                        dbc.Card(
                            dbc.CardBody(
                                html.Div(
                                    [

                                        html.Span(
                                            "●",
                                            style={
                                                "color": "red",
                                                "fontSize": "1.5rem",
                                                "marginRight": "8px"
                                            }
                                        ),

                                        html.Span(
                                            id="selected-date-text",
                                            style={
                                                "fontWeight": "bold",
                                                "marginRight": "8px",
                                                "color": "#555"
                                            }
                                        ),

                                        html.P(
                                            "Click the vortex curve to explore temperatures on different days.",
                                            style={
                                                "fontSize": "0.92rem",
                                                "marginBottom": "0px",
                                                "color": "#555"
                                            }
                                        ),

                                    ],
                                    style={
                                        "display": "flex",
                                        "alignItems": "center",
                                        "gap": "6px",
                                        "flexWrap": "wrap"
                                    }
                                )
                            ),
                            className="shadow-sm mb-3"
                        ),

                        dcc.Store(id="selected-date-store", data=default_date),
                        dcc.Store(id="window-size-store", data={"width": 1200, "height": 800}),
                        dcc.Interval(id="window-size-trigger", interval=100, n_intervals=0, max_intervals=1),

                        dbc.Card(
                            dbc.CardBody(
                                html.Div(
                                    html.Div(
                                        dcc.Graph(
                                            id="vortex-graph",
                                            config={"responsive": True}
                                        ),
                                        id="vortex-graph-inner",
                                        style={"minWidth": "100%"}
                                    ),
                                    style={
                                        "width": "100%",
                                        "overflowX": "auto",
                                        "overflowY": "hidden"
                                    }
                                ),
                                style={"padding": "0.5rem"}
                            ),
                            className="shadow-sm mb-3"
                        ),

                        dbc.Card(
                            dbc.CardBody(
                                dcc.Graph(
                                    id="map-graph",
                                    style={"width": "100%"},
                                    config={"responsive": True}
                                ),
                                style={"padding": "0 0.2rem 0 0.2rem"}
                            ),
                            className="shadow-sm"
                        ),

                    ],
                    xs=12,
                    md=9
                )
            ],
            className="g-3"
        )
    ],
    fluid=True
)

# ###########################################################################
# CALLBACK: Window width for map marker size
# ###########################################################################
app.clientside_callback(
    """
    function(n_intervals) {
        return {
            width: window.innerWidth,
            height: window.innerHeight
        };
    }
    """,
    Output("window-size-store", "data"),
    Input("window-size-trigger", "n_intervals")
)


# ###########################################################################
# CALLBACK: Vortex line graph
# ###########################################################################
#
# This callback builds the main vortex strength visualization.
# The graph changes depending on which winters are selected and whether the user wants overlay or side-by-side view.
#
# The selected date marker and the official SSW event markers are also added here.
#
#

@app.callback(
    Output("vortex-graph", "figure"),
    Output("vortex-graph-inner", "style"),
    Input("winter-select", "value"),
    Input("comparison-mode", "value"),
    Input("selected-date-store", "data")
)
def update_vortex_graph(selected_winters, mode, selected_date):
    if not selected_winters:

        fig = go.Figure()

        fig.update_layout(
            height=280,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            annotations=[
                dict(
                    text="Select one or more winters to display the vortex strength curve",
                    x=0.5,
                    y=0.5,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=18, color="#2a3f5f")
                )
            ]
        )

        return fig, {"minWidth": "100%"}

    selected_winters = sorted(selected_winters)

    filtered = df_vortex[df_vortex["winter"].isin(selected_winters)].copy()
    filtered["date_str"] = filtered["date"].dt.strftime("%Y-%m-%d")

    y_min = df_vortex["vortex_strength"].min()
    y_max = df_vortex["vortex_strength"].max()

    if mode == "separate":
        n = len(selected_winters)
        horizontal_spacing = 0.006 if n > 1 else 0

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
                    hovertemplate=(
                        "Date: %{customdata[0]}<br>"
                        "Vortex strength: %{y:.1f} m/s<br>"
                        "Click to update map"
                        "<extra></extra>"
                    ),
                    showlegend=False
                ),
                row=1,
                col=i
            )

            fig.update_xaxes(
                tickformat="%b %d",
                dtick="M1",
                row=1,
                col=i
            )

            fig.update_yaxes(range=[y_min, y_max], row=1, col=i)

            if i > 1:
                fig.update_yaxes(showticklabels=False, row=1, col=i)

        fig.update_yaxes(title_text="Vortex strength (m/s)", row=1, col=1)

        fig.update_layout(
            title=dict(
                text="Polar vortex  on winter seasons",
                x=0.05,
                xanchor="left"
            )
        )

    else:
        if len(selected_winters) == 1:
            title = f"Polar vortex strength on winter {selected_winters[0]}"
        else:
            title = "Polar vortex strength comparison"

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

        fig.update_traces(
            hovertemplate=(
                "Winter: %{fullData.name}<br>"
                "Date: %{customdata[0]}<br>"
                "Vortex strength: %{y:.1f} m/s<br>"
                "Click to update map"
                "<extra></extra>"
            )
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
                    customdata=selected_row[["date_str"]],
                    hovertemplate=(
                        "Selected date<br>"
                        "Date: %{customdata[0]}<br>"
                        "Vortex strength: %{y:.1f} m/s"
                        "<extra></extra>"
                    ),
                    showlegend=False
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
                    hovertemplate=(
                        "Selected date<br>"
                        "Date: %{customdata[0]}<br>"
                        "Vortex strength: %{y:.1f} m/s"
                        "<extra></extra>"
                    ),
                    showlegend=False
                )
            )
    
    # ###########################################################################
    # SSW EVENT MARKERS
    # ###########################################################################
    ssw_filtered = df_ssw[df_ssw["winter"].isin(selected_winters)].copy()

    if not ssw_filtered.empty:
        ssw_points = ssw_filtered.merge(
            df_vortex[["date", "winter", "winter_date", "vortex_strength"]],
            on=["date", "winter", "winter_date"],
            how="inner"
        )

        ssw_points["date_str"] = ssw_points["date"].dt.strftime("%Y-%m-%d")

        if mode == "separate":
            for winter in selected_winters:
                ssw_winter = ssw_points[ssw_points["winter"] == winter]

                if ssw_winter.empty:
                    continue

                col = selected_winters.index(winter) + 1

                fig.add_trace(
                    go.Scatter(
                        x=ssw_winter["winter_date"],
                        y=ssw_winter["vortex_strength"],
                        mode="markers",
                        marker=dict(color="blue", size=10, symbol="circle"),
                        name="Official SSW event",
                        customdata=ssw_winter[["date_str", "source"]],
                        hovertemplate=(
                            "Official SSW event<br>"
                            "Date: %{customdata[0]}<br>"
                            "Source: %{customdata[1]}<br>"
                            "Vortex strength: %{y:.1f} m/s<br>"
                            "Click to update map"
                            "<extra></extra>"
                        ),
                        showlegend=False
                    ),
                    row=1,
                    col=col
                )
        else:
            fig.add_trace(
                go.Scatter(
                    x=ssw_points["winter_date"],
                    y=ssw_points["vortex_strength"],
                    mode="markers",
                    marker=dict(color="blue", size=10, symbol="circle"),
                    name="Official SSW event",
                    customdata=ssw_points[["date_str", "source"]],
                    hovertemplate=(
                        "Official SSW event<br>"
                        "Date: %{customdata[0]}<br>"
                        "Source: %{customdata[1]}<br>"
                        "Vortex strength: %{y:.1f} m/s<br>"
                        "Click to update map"
                        "<extra></extra>"
                    ),
                    showlegend=False
                )
            )

    fig.update_layout(
        width=None,
        autosize=True,
        height=280,
        hovermode="closest",
        clickmode="event+select",
        showlegend=(mode == "overlay" and len(selected_winters) > 1),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.04,
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.85)"
        ),
        margin=dict(
            l=45,
            r=120 if mode == "overlay" else 20,
            t=75,
            b=55
        ),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig.update_xaxes(
        tickformat="%b %d",
        dtick="M1",
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        title=None
    )

    fig.update_yaxes(
        range=[y_min-2, y_max],
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor="rgba(0,0,0,0.08)"
    )

    if mode == "separate":
        min_subplot_width = 170
        min_width = max(100, len(selected_winters) * min_subplot_width)
        graph_style = {"minWidth": f"{min_width}px"}
    else:
        graph_style = {"minWidth": "100%"}

    return fig, graph_style

    


 

# ###########################################################################
# CALLBACK:  STORE THE SELECTED DATE
# ###########################################################################
#
# This callback handles the interaction logic between the controls, the vortex curve and the temperature map.
#
# The selected date can come either from clicking the vortex curve or from selecting an official SSW event from the dropdown menu.

@app.callback(
    Output("selected-date-store", "data"),
    Output("winter-select", "value"),
    Input("vortex-graph", "clickData"),
    Input("ssw-event-select", "value"),
    prevent_initial_call=True
)
def store_selected_date(clickData, selected_event_date):
    ctx = dash.callback_context

    if not ctx.triggered:
        return default_date, ["2024-2025"]

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == "ssw-event-select" and selected_event_date:
        selected_ts = pd.Timestamp(selected_event_date)

        event_row = df_ssw[df_ssw["date"] == selected_ts]

        if not event_row.empty:
            event_winter = event_row["winter"].iloc[0]
            return selected_event_date, [event_winter]

        return selected_event_date, ["2024-2025"]

    if trigger_id == "vortex-graph" and clickData is not None:
        return clickData["points"][0]["customdata"][0], dash.no_update

    return default_date, dash.no_update


# ###########################################################################
#  CALLBACK: UPDATE THE TEMPERATURE MAP
# ###########################################################################
#
# The map updates whenever the selected date or map settings change.
# Only the temperature file for the selected year is loaded, because the full dataset would be unnecessarily heavy for the app.
#
# The map can show either the actual temperatures or the difference from the long-term mean temperature of that calendar day.
#


@app.callback(
    Output("map-graph", "figure"),
    Output("selected-date-text", "children"),
    Input("selected-date-store", "data"),
    Input("map-variable", "value"),
    Input("grid-resolution", "value"),
    Input("window-size-store", "data"),
)
def update_map(selected_date, map_variable, grid_resolution, window_size):

    selected_ts = pd.Timestamp(selected_date)
    year = selected_ts.year

    file_path = temp_path / f"temp_{year}_{grid_resolution}.csv"

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

    df_clim = load_climatology(grid_resolution)

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

    fig.update_layout(
    title=dict(
        text=title,
        y=0.96,
        x=0.05,
        xanchor="left",
        yanchor="top"
    )
)

    window_width = 1200
    if window_size and "width" in window_size:
        window_width = window_size["width"]
    
    available_width = window_width - 300

    if grid_resolution == "5deg":
        marker_size = max(7, min(14, available_width / 100))
    else:
        marker_size = max(3, min(7, available_width / 220))

    fig.update_traces(
        marker=dict(size=marker_size, opacity=0.9)
    )

    if map_variable == "temp_anomaly":
        fig.update_traces(
            hovertemplate=(
                "Latitude: %{lat:.1f}<br>"
                "Longitude: %{lon:.1f}<br>"
                "Temperature anomaly: %{marker.color:.1f} °C<br>"
                "<extra></extra>"
            )
        )
    else:
        fig.update_traces(
            hovertemplate=(
                "Latitude: %{lat:.1f}<br>"
                "Longitude: %{lon:.1f}<br>"
                "Temperature: %{marker.color:.1f} °C"
                "<extra></extra>"
            )
        )

    fig.update_geos(
        showcoastlines=True,
        coastlinecolor="rgba(0,0,0,0.35)",
        showland=True,
        landcolor="white",
        showocean=True,
        oceancolor="white",
        showcountries=True,
        countrycolor="rgba(0,0,0,0.20)",
        lataxis_range=[25, 90]
    )

    
    fig.update_layout(
        height=380,
        margin=dict(l=10, r=45, t=0, b=0),
        paper_bgcolor="white",
        plot_bgcolor="white",
        coloraxis_colorbar=dict(
            title="°C",
            len=0.75,
            y=0.5
        )
    )

    return fig, f"Selected date: {selected_date}"


# ###########################################################################
# START THE APP
# ###########################################################################
#
# Debug mode was useful during development because this project went through many small iterative changes and testing phases.

if __name__ == "__main__":
    app.run(debug=False)
