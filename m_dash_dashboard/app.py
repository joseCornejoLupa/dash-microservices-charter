"""
Multi-Tabbed Plotly Dash Application for Experimental Data Analysis
Energy-efficient design: loads data on-demand only after experiment selection
"""

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from data_loader import DataLoader
import os
from pathlib import Path

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Experimental Data Analysis Dashboard"

# Initialize data loader
ROOT_DIR = (
    "/home/josec/green_computing/microservices/historyexecutions/experiments-data"
)
data_loader = DataLoader(ROOT_DIR)

# Application layout
app.layout = html.Div(
    [
        html.H1(
            "Experimental Data Analysis Dashboard",
            style={"textAlign": "center", "color": "#2c3e50", "marginBottom": 30},
        ),
        # Control Panel
        html.Div(
            [
                html.H3("Control Panel", style={"color": "#34495e"}),
                html.Div(
                    [
                        # Component Filter
                        html.Div(
                            [
                                html.Label("Component:", style={"fontWeight": "bold"}),
                                dcc.Dropdown(
                                    id="component-dropdown",
                                    options=[],
                                    placeholder="Select Component",
                                    style={"width": "200px"},
                                ),
                            ],
                            style={"display": "inline-block", "marginRight": 20},
                        ),
                        # Intensity Filter
                        html.Div(
                            [
                                html.Label("Intensity:", style={"fontWeight": "bold"}),
                                dcc.Dropdown(
                                    id="intensity-dropdown",
                                    options=[],
                                    placeholder="Select Intensity",
                                    style={"width": "200px"},
                                ),
                            ],
                            style={"display": "inline-block", "marginRight": 20},
                        ),
                        # Experiment Selector
                        html.Div(
                            [
                                html.Label("Experiment:", style={"fontWeight": "bold"}),
                                dcc.Dropdown(
                                    id="experiment-dropdown",
                                    options=[],
                                    placeholder="Select Experiment",
                                    style={"width": "400px"},
                                ),
                            ],
                            style={"display": "inline-block", "marginRight": 20},
                        ),
                    ],
                    style={"marginBottom": 20},
                ),
            ],
            style={
                "backgroundColor": "#ecf0f1",
                "padding": "20px",
                "borderRadius": "5px",
                "marginBottom": 20,
            },
        ),
        # Tabs
        dcc.Tabs(
            id="tabs",
            value="tab-energy",
            children=[
                # Tab 1: Energy Analysis
                dcc.Tab(
                    label="Energy Analysis",
                    value="tab-energy",
                    children=[
                        html.Div(
                            [
                                html.H3(
                                    "Energy Analysis",
                                    style={"color": "#34495e", "marginTop": 20},
                                ),
                                # Energy source selector
                                html.Div(
                                    [
                                        html.Label(
                                            "Energy Data Source:",
                                            style={
                                                "fontWeight": "bold",
                                                "marginRight": 10,
                                            },
                                        ),
                                        dcc.RadioItems(
                                            id="energy-source-radio",
                                            options=[
                                                {
                                                    "label": "Ecofloc",
                                                    "value": "ecofloc",
                                                },
                                                {
                                                    "label": "Scaphandre",
                                                    "value": "scaphandre",
                                                },
                                                {
                                                    "label": "Both",
                                                    "value": "both",
                                                },
                                            ],
                                            value="ecofloc",
                                            inline=True,
                                            style={"marginBottom": 20},
                                        ),
                                    ],
                                    style={"marginBottom": 20},
                                ),
                                # Row 1: Main Energy Evolution by Node
                                html.Div(
                                    [
                                        dcc.Graph(id="energy-evolution-chart"),
                                    ]
                                ),
                                # Row 2: Component-specific energy charts
                                html.Div(
                                    [
                                        html.H4(
                                            "Energy Evolution by Component",
                                            style={
                                                "color": "#34495e",
                                                "marginTop": 30,
                                                "marginBottom": 20,
                                            },
                                        ),
                                        dcc.Graph(id="cpu-energy-chart"),
                                        dcc.Graph(id="ram-energy-chart"),
                                        dcc.Graph(id="sd-energy-chart"),
                                        dcc.Graph(id="nic-energy-chart"),
                                    ],
                                    style={"marginTop": 20},
                                ),
                                # Row 3: Process Energy Consumption per-node bar charts
                                html.Div(
                                    [
                                        html.H4(
                                            "Process Energy Consumption",
                                            style={
                                                "color": "#34495e",
                                                "marginTop": 30,
                                                "marginBottom": 20,
                                            },
                                        ),
                                        html.Div(id="process-energy-bars-container"),
                                    ],
                                    style={"marginTop": 20},
                                ),
                                # Row 4: Energy Distribution by Process (pie charts)
                                html.Div(
                                    [
                                        dcc.Graph(id="energy-distribution-chart"),
                                    ],
                                    style={"marginTop": 20},
                                ),
                                # Row 5: Cumulative Energy by Component (bar charts)
                                html.Div(
                                    [
                                        dcc.Graph(id="cumulative-energy-chart"),
                                    ],
                                    style={"marginTop": 20},
                                ),
                            ],
                            style={"padding": 20},
                        )
                    ],
                ),
                # Tab 2: Benchmark Performance
                dcc.Tab(
                    label="Benchmark Performance",
                    value="tab-benchmark",
                    children=[
                        html.Div(
                            [
                                html.H3(
                                    "Benchmark Performance",
                                    style={"color": "#34495e", "marginTop": 20},
                                ),
                                # Benchmark charts
                                html.Div(
                                    [
                                        dcc.Graph(id="transaction-status-chart"),
                                    ]
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                dcc.Graph(id="response-time-chart"),
                                            ],
                                            style={
                                                "width": "48%",
                                                "display": "inline-block",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                dcc.Graph(id="load-intensity-chart"),
                                            ],
                                            style={
                                                "width": "48%",
                                                "display": "inline-block",
                                                "float": "right",
                                            },
                                        ),
                                    ]
                                ),
                            ],
                            style={"padding": 20},
                        )
                    ],
                ),
                # Tab 3: Averages
                dcc.Tab(
                    label="Averages",
                    value="tab-averages",
                    id="averages-tab",
                    disabled=True,
                    children=[
                        html.Div(
                            [
                                html.H3(
                                    "Averages Analysis",
                                    style={"color": "#34495e", "marginTop": 20},
                                ),
                                # Informational note about data source
                                html.Div(
                                    [
                                        html.Strong("Note: ", style={"color": "#2c3e50"}),
                                        "The charts on this tab display averages calculated exclusively from Ecofloc data.",
                                    ],
                                    style={
                                        "backgroundColor": "#d4edda",
                                        "color": "#155724",
                                        "padding": "12px 20px",
                                        "borderRadius": "5px",
                                        "border": "1px solid #c3e6cb",
                                        "marginBottom": 20,
                                        "fontSize": "14px",
                                    },
                                ),
                                # Experiment Information Display
                                html.Div(
                                    id="averages-experiment-info",
                                    style={"marginBottom": 20},
                                ),
                                # Energy Profile Pie Chart
                                html.Div(
                                    [
                                        dcc.Graph(id="averages-energy-profile-pie"),
                                    ]
                                ),
                                # Average Component Energy Breakdown Bar Chart
                                html.Div(
                                    [
                                        dcc.Graph(
                                            id="averages-component-breakdown-bar"
                                        ),
                                    ],
                                    style={"marginTop": 30},
                                ),
                                # Average Overall Energy Evolution Chart
                                html.Div(
                                    [
                                        html.H4(
                                            "Average Energy Evolution Over Time",
                                            style={
                                                "color": "#34495e",
                                                "marginTop": 30,
                                                "marginBottom": 20,
                                            },
                                        ),
                                        dcc.Graph(id="averages-overall-energy-evolution"),
                                    ],
                                    style={"marginTop": 30},
                                ),
                                # Average Energy Evolution by Component Charts
                                html.Div(
                                    [
                                        html.H4(
                                            "Average Component Energy Evolution",
                                            style={
                                                "color": "#34495e",
                                                "marginTop": 30,
                                                "marginBottom": 20,
                                            },
                                        ),
                                        dcc.Graph(id="averages-cpu-energy-evolution"),
                                        dcc.Graph(id="averages-ram-energy-evolution"),
                                        dcc.Graph(id="averages-sd-energy-evolution"),
                                        dcc.Graph(id="averages-nic-energy-evolution"),
                                    ],
                                    style={"marginTop": 30},
                                ),
                            ],
                            style={"padding": 20},
                        )
                    ],
                ),
                # Tab 4: Correlation
                dcc.Tab(
                    label="Correlation",
                    value="tab-correlation",
                    children=[
                        html.Div(
                            [
                                html.H3(
                                    "Energy and Performance Correlation",
                                    style={"color": "#34495e", "marginTop": 20},
                                ),
                                # Energy source selector for correlation tab
                                html.Div(
                                    [
                                        html.Label(
                                            "Energy Data Source:",
                                            style={
                                                "fontWeight": "bold",
                                                "marginRight": 10,
                                            },
                                        ),
                                        dcc.RadioItems(
                                            id="correlation-energy-source-radio",
                                            options=[
                                                {
                                                    "label": "Ecofloc",
                                                    "value": "ecofloc",
                                                },
                                                {
                                                    "label": "Scaphandre",
                                                    "value": "scaphandre",
                                                },
                                            ],
                                            value="ecofloc",
                                            inline=True,
                                            style={"marginBottom": 20},
                                        ),
                                    ],
                                    style={"marginBottom": 20},
                                ),
                                # Correlation charts
                                html.Div(
                                    [
                                        dcc.Graph(id="correlation-energy-chart"),
                                    ]
                                ),
                                html.Div(
                                    [
                                        dcc.Graph(id="correlation-transaction-chart"),
                                    ]
                                ),
                                html.Div(
                                    [
                                        dcc.Graph(id="correlation-response-time-chart"),
                                    ]
                                ),
                                # Energy Profile Pie Charts Section
                                html.Div(
                                    [
                                        html.H4(
                                            "Energy Profile by Transaction Outcome",
                                            style={
                                                "color": "#34495e",
                                                "marginTop": 30,
                                                "marginBottom": 20,
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        dcc.Graph(
                                                            id="energy-profile-successful-pie"
                                                        ),
                                                    ],
                                                    style={
                                                        "width": "32%",
                                                        "display": "inline-block",
                                                        "marginRight": "1%",
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        dcc.Graph(
                                                            id="energy-profile-failed-pie"
                                                        ),
                                                    ],
                                                    style={
                                                        "width": "32%",
                                                        "display": "inline-block",
                                                        "marginRight": "1%",
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        dcc.Graph(
                                                            id="energy-profile-dropped-pie"
                                                        ),
                                                    ],
                                                    style={
                                                        "width": "32%",
                                                        "display": "inline-block",
                                                    },
                                                ),
                                            ]
                                        ),
                                    ]
                                ),
                            ],
                            style={"padding": 20},
                        )
                    ],
                ),
            ],
        ),
        # Hidden div to store loaded data
        dcc.Store(id="energy-data-store"),
        dcc.Store(id="benchmark-data-store"),
        dcc.Store(id="current-component-store"),
        dcc.Store(id="current-intensity-store"),
        # Store for component-specific energy data
        dcc.Store(id="component-energy-data-store"),
        # Store for synchronized hover position
        dcc.Store(id="hover-position-store"),
        # Store for averages data (all experiments in category)
        dcc.Store(id="averages-data-store"),
    ],
    style={
        "fontFamily": "Arial, sans-serif",
        "margin": "0 auto",
        "maxWidth": "1400px",
        "padding": 20,
    },
)


# Callback to populate component dropdown on load
@app.callback(
    Output("component-dropdown", "options"), Input("component-dropdown", "id")
)
def populate_components(_):
    """Populate component dropdown with available components"""
    components = data_loader.get_available_components()
    return [{"label": c.upper(), "value": c} for c in components]


# Callback to populate intensity dropdown based on component
@app.callback(
    Output("intensity-dropdown", "options"),
    Output("intensity-dropdown", "value"),
    Input("component-dropdown", "value"),
)
def populate_intensities(component):
    """Populate intensity dropdown based on selected component"""
    if not component:
        return [], None

    # For unified component, include 'specific-scenarios' in addition to standard intensities
    if component == "unified":
        options = [
            {"label": "LOW", "value": "low"},
            {"label": "MED", "value": "med"},
            {"label": "HIGH", "value": "high"},
            {"label": "SPECIFIC-SCENARIOS", "value": "specific-scenarios"},
        ]
        return options, None

    # For other components, use the standard intensities from data_loader
    intensities = data_loader.get_available_intensities(component)
    options = [{"label": i.upper(), "value": i} for i in intensities]
    return options, None


# Callback to populate experiment dropdown based on component and intensity
# Also controls the Averages tab disabled state
@app.callback(
    Output("experiment-dropdown", "options"),
    Output("experiment-dropdown", "value"),
    Output("averages-tab", "disabled"),
    Input("component-dropdown", "value"),
    Input("intensity-dropdown", "value"),
)
def populate_experiments(component, intensity):
    """Populate experiment dropdown based on component and intensity"""
    if not component or not intensity:
        return [], None, True

    experiments = data_loader.get_available_experiments(component, intensity)

    # Enable averages tab if we have valid component and intensity
    averages_tab_disabled = not (component and intensity)

    return experiments, None, averages_tab_disabled


# Callback to load data when experiment is selected
@app.callback(
    Output("energy-data-store", "data"),
    Output("benchmark-data-store", "data"),
    Output("current-component-store", "data"),
    Output("current-intensity-store", "data"),
    Input("experiment-dropdown", "value"),
    State("component-dropdown", "value"),
    State("intensity-dropdown", "value"),
)
def load_experiment_data(experiment_path, component, intensity):
    """
    Load data on-demand when experiment is selected
    Energy-efficient: only loads when needed
    """
    if not experiment_path or not component or not intensity:
        return None, None, None, None

    # Load energy data (both sources)
    ecofloc_df = data_loader.load_ecofloc_data(experiment_path, component)
    scaphandre_df = data_loader.load_scaphandre_data(experiment_path)

    # Load benchmark data
    limbo_df = data_loader.load_limbo_data(experiment_path, intensity)

    # Convert to dict for storage
    energy_data = {
        "ecofloc": ecofloc_df.to_dict("records") if not ecofloc_df.empty else [],
        "scaphandre": (
            scaphandre_df.to_dict("records") if not scaphandre_df.empty else []
        ),
    }

    benchmark_data = limbo_df.to_dict("records") if not limbo_df.empty else []

    return energy_data, benchmark_data, component, intensity


# Callback to load component-specific energy data
@app.callback(
    Output("component-energy-data-store", "data"),
    Input("experiment-dropdown", "value"),
)
def load_component_energy_data(experiment_path):
    """
    Load component-specific energy data for all four components
    """
    if not experiment_path:
        return None

    # Load data for each component
    component_data = {}
    for component in ["cpu", "ram", "sd", "nic"]:
        df = data_loader.load_ecofloc_component_data(experiment_path, component)
        component_data[component] = df.to_dict("records") if not df.empty else []

    return component_data


# Callback to update CPU energy chart
@app.callback(
    Output("cpu-energy-chart", "figure"),
    Input("component-energy-data-store", "data"),
)
def update_cpu_energy_chart(component_data):
    """Update CPU energy evolution time-series chart"""
    if not component_data or "cpu" not in component_data:
        return create_empty_figure("No CPU data available")

    data_records = component_data["cpu"]
    if not data_records:
        return create_empty_figure("No CPU data available")

    df = pd.DataFrame(data_records)

    if "elapsed_seconds" not in df.columns or df.empty:
        return create_empty_figure("No CPU data available")

    fig = go.Figure()

    # Create a line for each node
    for node in df["node_name"].unique():
        node_data = df[df["node_name"] == node]
        fig.add_trace(
            go.Scatter(
                x=node_data["elapsed_seconds"],
                y=node_data["energy_value"],
                mode="lines+markers",
                name=node,
                line=dict(width=2),
                marker=dict(size=4),
            )
        )

    fig.update_layout(
        title="CPU Energy Evolution",
        xaxis_title="Time (seconds)",
        yaxis_title="Energy (Joules)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=350,
    )

    return fig


# Callback to update RAM energy chart
@app.callback(
    Output("ram-energy-chart", "figure"),
    Input("component-energy-data-store", "data"),
)
def update_ram_energy_chart(component_data):
    """Update RAM energy evolution time-series chart"""
    if not component_data or "ram" not in component_data:
        return create_empty_figure("No RAM data available")

    data_records = component_data["ram"]
    if not data_records:
        return create_empty_figure("No RAM data available")

    df = pd.DataFrame(data_records)

    if "elapsed_seconds" not in df.columns or df.empty:
        return create_empty_figure("No RAM data available")

    fig = go.Figure()

    # Create a line for each node
    for node in df["node_name"].unique():
        node_data = df[df["node_name"] == node]
        fig.add_trace(
            go.Scatter(
                x=node_data["elapsed_seconds"],
                y=node_data["energy_value"],
                mode="lines+markers",
                name=node,
                line=dict(width=2),
                marker=dict(size=4),
            )
        )

    fig.update_layout(
        title="RAM Energy Evolution",
        xaxis_title="Time (seconds)",
        yaxis_title="Energy (Joules)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=350,
    )

    return fig


# Callback to update SD energy chart
@app.callback(
    Output("sd-energy-chart", "figure"),
    Input("component-energy-data-store", "data"),
)
def update_sd_energy_chart(component_data):
    """Update SD (Storage) energy evolution time-series chart"""
    if not component_data or "sd" not in component_data:
        return create_empty_figure("No SD data available")

    data_records = component_data["sd"]
    if not data_records:
        return create_empty_figure("No SD data available")

    df = pd.DataFrame(data_records)

    if "elapsed_seconds" not in df.columns or df.empty:
        return create_empty_figure("No SD data available")

    fig = go.Figure()

    # Create a line for each node
    for node in df["node_name"].unique():
        node_data = df[df["node_name"] == node]
        fig.add_trace(
            go.Scatter(
                x=node_data["elapsed_seconds"],
                y=node_data["energy_value"],
                mode="lines+markers",
                name=node,
                line=dict(width=2),
                marker=dict(size=4),
            )
        )

    fig.update_layout(
        title="SD Energy Evolution",
        xaxis_title="Time (seconds)",
        yaxis_title="Energy (Joules)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=350,
    )

    return fig


# Callback to update NIC energy chart
@app.callback(
    Output("nic-energy-chart", "figure"),
    Input("component-energy-data-store", "data"),
)
def update_nic_energy_chart(component_data):
    """Update NIC (Network) energy evolution time-series chart"""
    if not component_data or "nic" not in component_data:
        return create_empty_figure("No NIC data available")

    data_records = component_data["nic"]
    if not data_records:
        return create_empty_figure("No NIC data available")

    df = pd.DataFrame(data_records)

    if "elapsed_seconds" not in df.columns or df.empty:
        return create_empty_figure("No NIC data available")

    fig = go.Figure()

    # Create a line for each node
    for node in df["node_name"].unique():
        node_data = df[df["node_name"] == node]
        fig.add_trace(
            go.Scatter(
                x=node_data["elapsed_seconds"],
                y=node_data["energy_value"],
                mode="lines+markers",
                name=node,
                line=dict(width=2),
                marker=dict(size=4),
            )
        )

    fig.update_layout(
        title="NIC Energy Evolution",
        xaxis_title="Time (seconds)",
        yaxis_title="Energy (Joules)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=350,
    )

    return fig


# Callback to update energy evolution chart
@app.callback(
    Output("energy-evolution-chart", "figure"),
    Input("energy-data-store", "data"),
    Input("energy-source-radio", "value"),
)
def update_energy_evolution(energy_data, source):
    """Update energy evolution time-series chart"""
    if not energy_data:
        return create_empty_figure("No data available")

    fig = go.Figure()

    # Handle "both" option - show both sources
    if source == "both":
        # Check if we have both data sources
        has_ecofloc = "ecofloc" in energy_data and energy_data["ecofloc"]
        has_scaphandre = "scaphandre" in energy_data and energy_data["scaphandre"]

        if not has_ecofloc and not has_scaphandre:
            return create_empty_figure("No data available")

        # Process Ecofloc data (solid lines)
        if has_ecofloc:
            df_eco = pd.DataFrame(energy_data["ecofloc"])
            if "elapsed_seconds" in df_eco.columns:
                for node in df_eco["node_name"].unique():
                    node_data = df_eco[df_eco["node_name"] == node]
                    fig.add_trace(
                        go.Scatter(
                            x=node_data["elapsed_seconds"],
                            y=node_data["energy_value"],
                            mode="lines+markers",
                            name=f"{node} (Ecofloc)",
                            line=dict(width=2, dash="solid"),
                            marker=dict(size=4),
                        )
                    )

        # Process Scaphandre data (dotted lines)
        if has_scaphandre:
            df_scaph = pd.DataFrame(energy_data["scaphandre"])
            if "elapsed_seconds" in df_scaph.columns:
                for node in df_scaph["node_name"].unique():
                    node_data = df_scaph[df_scaph["node_name"] == node]
                    fig.add_trace(
                        go.Scatter(
                            x=node_data["elapsed_seconds"],
                            y=node_data["energy_value"],
                            mode="lines+markers",
                            name=f"{node} (Scaphandre)",
                            line=dict(width=2, dash="dot"),
                            marker=dict(size=4, symbol="diamond"),
                        )
                    )

        fig.update_layout(
            title="Energy Evolution Over Time (Both Sources)",
            xaxis_title="Time (seconds)",
            yaxis_title="Energy (Mixed Units: Joules for Ecofloc, Watts for Scaphandre)",
            hovermode="x unified",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            height=600,  # Increased height for better visibility
        )

        return fig

    # Handle single source (original logic)
    if source not in energy_data:
        return create_empty_figure("No data available")

    data_records = energy_data[source]
    if not data_records:
        return create_empty_figure(f"No {source} data available")

    df = pd.DataFrame(data_records)

    # Use elapsed_seconds for x-axis
    if "elapsed_seconds" not in df.columns:
        return create_empty_figure(f"No elapsed_seconds data available for {source}")

    # Create a line for each node
    for node in df["node_name"].unique():
        node_data = df[df["node_name"] == node]
        fig.add_trace(
            go.Scatter(
                x=node_data["elapsed_seconds"],
                y=node_data["energy_value"],
                mode="lines+markers",
                name=node,
                line=dict(width=2),
                marker=dict(size=4),
            )
        )

    fig.update_layout(
        title=f"Energy Evolution Over Time ({source.capitalize()})",
        xaxis_title="Time (seconds)",
        yaxis_title="Energy (Watts)" if source == "scaphandre" else "Energy (Joules)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400,
    )

    return fig


# Callback to update energy distribution pie chart
@app.callback(
    Output("energy-distribution-chart", "figure"),
    Input("energy-data-store", "data"),
    Input("energy-source-radio", "value"),
    Input("experiment-dropdown", "value"),
    State("current-component-store", "data"),
)
def update_energy_distribution(energy_data, source, experiment_path, component):
    """Update energy distribution by node pie chart with per-node process breakdowns"""
    if not energy_data or source not in energy_data:
        return create_empty_figure("No data available")

    # Only use ecofloc for PID-level data
    if source == "scaphandre":
        # For scaphandre, just show the original single pie chart
        data_records = energy_data[source]
        if not data_records:
            return create_empty_figure(f"No {source} data available")

        df = pd.DataFrame(data_records)
        energy_by_node = df.groupby("node_name")["energy_value"].sum().reset_index()

        fig = px.pie(
            energy_by_node,
            values="energy_value",
            names="node_name",
            title="Energy Distribution by Node",
            hole=0.3,
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(height=400)

        return fig

    # For ecofloc, create multiple pie charts
    if source == "both":
        source = "ecofloc"

    data_records = energy_data[source]
    if not data_records:
        return create_empty_figure(f"No {source} data available")

    if not experiment_path or not component:
        # Fallback to single pie chart if we don't have experiment info
        df = pd.DataFrame(data_records)
        energy_by_node = df.groupby("node_name")["energy_value"].sum().reset_index()

        fig = px.pie(
            energy_by_node,
            values="energy_value",
            names="node_name",
            title="Energy Distribution by Node",
            hole=0.3,
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(height=400)

        return fig

    df = pd.DataFrame(data_records)

    # Calculate total energy per node for main pie chart
    energy_by_node = df.groupby("node_name")["energy_value"].sum().reset_index()
    nodes = energy_by_node["node_name"].tolist()
    num_nodes = len(nodes)

    # Try to load PID-level data for process breakdowns
    try:
        pids_df = data_loader.load_informe_pids(experiment_path)
        pid_energy_df = data_loader.load_ecofloc_pid_data(experiment_path, component)

        if not pids_df.empty and not pid_energy_df.empty:
            # Merge PID data with process names
            merged_df = pid_energy_df.merge(
                pids_df, on=["node_name", "pid"], how="inner"
            )

            if not merged_df.empty:
                # Calculate process-level energy per node
                process_energy = (
                    merged_df.groupby(["node_name", "name_pid"])["energy_value"]
                    .sum()
                    .reset_index()
                )

                # Create subplots: 1 main pie + 1 per node
                # Calculate rows and columns for layout
                total_charts = num_nodes + 1
                cols = min(3, total_charts)
                rows = (total_charts + cols - 1) // cols

                specs = [[{"type": "pie"} for _ in range(cols)] for _ in range(rows)]

                fig = make_subplots(
                    rows=rows,
                    cols=cols,
                    specs=specs,
                    subplot_titles=["Energy Distribution by Node"]
                    + [f"Process Distribution on {node}" for node in nodes],
                )

                # Add main pie chart (node distribution)
                fig.add_trace(
                    go.Pie(
                        labels=energy_by_node["node_name"],
                        values=energy_by_node["energy_value"],
                        name="Node Distribution",
                        hole=0.3,
                        textposition="inside",
                        textinfo="percent+label",
                    ),
                    row=1,
                    col=1,
                )

                # Add per-node process distribution pie charts
                for idx, node in enumerate(nodes):
                    node_process_data = process_energy[
                        process_energy["node_name"] == node
                    ]

                    # Calculate position in grid
                    chart_idx = (
                        idx + 2
                    )  # +2 because idx starts at 0 and main chart is at 1
                    row = (chart_idx - 1) // cols + 1
                    col = (chart_idx - 1) % cols + 1

                    fig.add_trace(
                        go.Pie(
                            labels=node_process_data["name_pid"],
                            values=node_process_data["energy_value"],
                            name=f"{node} Processes",
                            hole=0.3,
                            textposition="inside",
                            textinfo="percent+label",
                        ),
                        row=row,
                        col=col,
                    )

                # Calculate appropriate height based on rows
                height = max(400, rows * 300)

                fig.update_layout(
                    height=height,
                    showlegend=False,
                    title_text="Energy Distribution Analysis",
                )

                return fig

    except Exception as e:
        print(f"Error creating multi-pie chart: {e}")
        # Fall back to simple pie chart

    # Fallback: simple single pie chart
    fig = px.pie(
        energy_by_node,
        values="energy_value",
        names="node_name",
        title="Energy Distribution by Node",
        hole=0.3,
    )

    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(height=400)

    return fig


# Callback to update cumulative energy bar chart
@app.callback(
    Output("cumulative-energy-chart", "figure"),
    Input("component-energy-data-store", "data"),
    Input("energy-source-radio", "value"),
)
def update_cumulative_energy(component_data, source):
    """Update cumulative energy per node bar chart with per-node component breakdowns"""

    # For scaphandre or if no component data, show simple chart
    if not component_data or source == "scaphandre":
        return create_empty_figure(
            "Component breakdown only available for Ecofloc source"
        )

    # Gather all nodes from component data
    all_nodes = set()
    component_dfs = {}

    for component in ["cpu", "ram", "sd", "nic"]:
        if component in component_data and component_data[component]:
            df = pd.DataFrame(component_data[component])
            if not df.empty and "node_name" in df.columns:
                component_dfs[component] = df
                all_nodes.update(df["node_name"].unique())

    if not all_nodes:
        return create_empty_figure("No component data available")

    nodes = sorted(list(all_nodes))
    num_nodes = len(nodes)

    # Create subplots - one bar chart per node
    fig = make_subplots(
        rows=num_nodes,
        cols=1,
        subplot_titles=[f"Component Energy on {node}" for node in nodes],
        vertical_spacing=0.15 / max(num_nodes, 1),
    )

    # For each node, create a horizontal bar chart showing component breakdown
    for idx, node in enumerate(nodes):
        component_energies = []
        component_names = []

        for component in ["cpu", "ram", "sd", "nic"]:
            if component in component_dfs:
                node_data = component_dfs[component][
                    component_dfs[component]["node_name"] == node
                ]
                total_energy = (
                    node_data["energy_value"].sum() if not node_data.empty else 0
                )
                component_energies.append(total_energy)
                component_names.append(component.upper())
            else:
                component_energies.append(0)
                component_names.append(component.upper())

        fig.add_trace(
            go.Bar(
                x=component_energies,
                y=component_names,
                orientation="h",
                name=node,
                showlegend=False,
                marker=dict(
                    color=component_energies,
                    colorscale="Viridis",
                ),
                text=[f"{e:.2f}" for e in component_energies],
                textposition="auto",
            ),
            row=idx + 1,
            col=1,
        )

        # Update x-axis label for bottom chart only
        if idx == num_nodes - 1:
            fig.update_xaxes(title_text="Total Energy (Joules)", row=idx + 1, col=1)
        else:
            fig.update_xaxes(row=idx + 1, col=1)

        fig.update_yaxes(title_text="Component", row=idx + 1, col=1)

    # Calculate appropriate height based on number of nodes
    height = max(400, num_nodes * 250)

    fig.update_layout(
        height=height, title_text="Component Energy Breakdown by Node", showlegend=False
    )

    return fig


# Callback to update process energy consumption per-node bar charts
@app.callback(
    Output("process-energy-bars-container", "children"),
    Input("energy-data-store", "data"),
    Input("energy-source-radio", "value"),
    Input("experiment-dropdown", "value"),
    State("current-component-store", "data"),
)
def update_process_energy_bars(energy_data, source, experiment_path, component):
    """Update process-level energy consumption as separate bar charts per node"""
    if not energy_data or not experiment_path or not component:
        return html.Div(
            "No data available",
            style={"textAlign": "center", "color": "gray", "padding": 20},
        )

    # Only use ecofloc for PID-level data (scaphandre doesn't have PID data)
    if source == "scaphandre":
        return html.Div(
            "Process-level energy data only available for Ecofloc source",
            style={"textAlign": "center", "color": "gray", "padding": 20},
        )

    if source == "both":
        # Use ecofloc data when "both" is selected
        source = "ecofloc"

    try:
        # Load informe_pids.csv
        pids_df = data_loader.load_informe_pids(experiment_path)

        if pids_df.empty:
            return html.Div(
                "No process information available (informe_pids.csv not found)",
                style={"textAlign": "center", "color": "gray", "padding": 20},
            )

        # Load per-PID energy data
        pid_energy_df = data_loader.load_ecofloc_pid_data(experiment_path, component)

        if pid_energy_df.empty:
            return html.Div(
                "No per-PID energy data available",
                style={"textAlign": "center", "color": "gray", "padding": 20},
            )

        # Merge PID data with process names
        merged_df = pid_energy_df.merge(pids_df, on=["node_name", "pid"], how="inner")

        if merged_df.empty:
            return html.Div(
                "No matching process data found",
                style={"textAlign": "center", "color": "gray", "padding": 20},
            )

        # Aggregate total energy by node and process
        aggregated = (
            merged_df.groupby(["node_name", "name_pid"])["energy_value"]
            .sum()
            .reset_index()
        )

        # Get unique nodes
        unique_nodes = aggregated["node_name"].unique()

        # Create a list to hold all the graph components
        graph_components = []

        # Create one bar chart for each node
        for node_name in unique_nodes:
            # Filter data for this specific node
            node_data = aggregated[aggregated["node_name"] == node_name]

            # Sort by energy value for better visualization
            node_data = node_data.sort_values("energy_value", ascending=False)

            # Create bar chart for this node
            fig = px.bar(
                node_data,
                x="name_pid",
                y="energy_value",
                title=f"Process Energy on Node: {node_name}",
                labels={"name_pid": "Process", "energy_value": "Energy (Joules)"},
            )

            fig.update_layout(
                height=400,
                xaxis_title="Process",
                yaxis_title="Energy (Joules)",
                hovermode="x unified",
                showlegend=False,
            )

            # Add this graph to the list
            graph_components.append(dcc.Graph(figure=fig))

        return graph_components

    except Exception as e:
        return html.Div(
            f"Error creating bar charts: {str(e)}",
            style={"textAlign": "center", "color": "red", "padding": 20},
        )


# Callback to populate node selector dropdown
@app.callback(
    Output("node-selector-dropdown", "options"),
    Output("node-selector-dropdown", "value"),
    Input("experiment-dropdown", "value"),
    State("current-component-store", "data"),
)
def populate_node_selector(experiment_path, component):
    """Populate node selector dropdown with available nodes from informe_pids.csv"""
    if not experiment_path or not component:
        return [], None

    try:
        # Load informe_pids.csv
        pids_df = data_loader.load_informe_pids(experiment_path)

        if pids_df.empty:
            return [], None

        # Get unique node names
        unique_nodes = sorted(pids_df["node_name"].unique())
        options = [{"label": node, "value": node} for node in unique_nodes]

        # Default to first node
        default_value = unique_nodes[0] if unique_nodes else None

        return options, default_value

    except Exception as e:
        print(f"Error populating node selector: {e}")
        return [], None


# Callback to update process energy time-series chart
@app.callback(
    Output("process-energy-timeseries", "figure"),
    Input("node-selector-dropdown", "value"),
    Input("experiment-dropdown", "value"),
    State("current-component-store", "data"),
)
def update_process_energy_timeseries(selected_node, experiment_path, component):
    """Update process-level energy time-series chart for selected node"""
    if not selected_node or not experiment_path or not component:
        return create_empty_figure("Select a node to view process energy evolution")

    try:
        # Load informe_pids.csv
        pids_df = data_loader.load_informe_pids(experiment_path)

        if pids_df.empty:
            return create_empty_figure(
                "No process information available (informe_pids.csv not found)"
            )

        # Load per-PID energy data
        pid_energy_df = data_loader.load_ecofloc_pid_data(experiment_path, component)

        if pid_energy_df.empty:
            return create_empty_figure("No per-PID energy data available")

        # Merge PID data with process names
        merged_df = pid_energy_df.merge(pids_df, on=["node_name", "pid"], how="inner")

        if merged_df.empty:
            return create_empty_figure("No matching process data found")

        # Filter data for selected node
        node_data = merged_df[merged_df["node_name"] == selected_node]

        if node_data.empty:
            return create_empty_figure(f"No data available for node: {selected_node}")

        # Calculate elapsed seconds from first timestamp
        min_timestamp = node_data["timestamp"].min()
        node_data = node_data.copy()
        node_data["elapsed_seconds"] = (
            node_data["timestamp"] - min_timestamp
        ).dt.total_seconds()

        # Create time-series chart with a line for each process
        fig = go.Figure()

        # Get unique processes for this node
        unique_processes = node_data["name_pid"].unique()

        for process_name in unique_processes:
            process_data = node_data[node_data["name_pid"] == process_name]

            fig.add_trace(
                go.Scatter(
                    x=process_data["elapsed_seconds"],
                    y=process_data["energy_value"],
                    mode="lines+markers",
                    name=process_name,
                    line=dict(width=2),
                    marker=dict(size=4),
                )
            )

        fig.update_layout(
            title=f"Process Energy Evolution on Node: {selected_node}",
            xaxis_title="Time (seconds)",
            yaxis_title="Energy (Joules)",
            hovermode="x unified",
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
            height=500,
        )

        return fig

    except Exception as e:
        return create_empty_figure(f"Error creating time-series chart: {str(e)}")


# Callback to update transaction status chart
@app.callback(
    Output("transaction-status-chart", "figure"), Input("benchmark-data-store", "data")
)
def update_transaction_status(benchmark_data):
    """Update transaction status time-series chart"""
    if not benchmark_data:
        return create_empty_figure("No benchmark data available")

    df = pd.DataFrame(benchmark_data)

    if df.empty or "target_time" not in df.columns:
        return create_empty_figure("No valid benchmark data")

    fig = go.Figure()

    # Add traces for each transaction type
    if "successful_transactions" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["target_time"],
                y=df["successful_transactions"],
                mode="lines+markers",
                name="Successful",
                line=dict(color="green", width=2),
                marker=dict(size=6),
            )
        )

    if "failed_transactions" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["target_time"],
                y=df["failed_transactions"],
                mode="lines+markers",
                name="Failed",
                line=dict(color="red", width=2),
                marker=dict(size=6),
            )
        )

    if "dropped_transactions" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["target_time"],
                y=df["dropped_transactions"],
                mode="lines+markers",
                name="Dropped",
                line=dict(color="orange", width=2),
                marker=dict(size=6),
            )
        )

    fig.update_layout(
        title="Transaction Status Over Time",
        xaxis_title="Target Time (s)",
        yaxis_title="Number of Transactions",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400,
    )

    return fig


# Callback to update response time chart
@app.callback(
    Output("response-time-chart", "figure"), Input("benchmark-data-store", "data")
)
def update_response_time(benchmark_data):
    """Update average response time chart"""
    if not benchmark_data:
        return create_empty_figure("No benchmark data available")

    df = pd.DataFrame(benchmark_data)

    if (
        df.empty
        or "target_time" not in df.columns
        or "avg_response_time" not in df.columns
    ):
        return create_empty_figure("No valid benchmark data")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["target_time"],
            y=df["avg_response_time"],
            mode="lines+markers",
            name="Avg Response Time",
            line=dict(color="blue", width=2),
            marker=dict(size=6),
            fill="tozeroy",
            fillcolor="rgba(0, 100, 255, 0.2)",
        )
    )

    fig.update_layout(
        title="Average Response Time",
        xaxis_title="Target Time (s)",
        yaxis_title="Response Time (s)",
        hovermode="x unified",
        height=400,
    )

    return fig


# Callback to update load intensity chart
@app.callback(
    Output("load-intensity-chart", "figure"), Input("benchmark-data-store", "data")
)
def update_load_intensity(benchmark_data):
    """Update load intensity chart"""
    if not benchmark_data:
        return create_empty_figure("No benchmark data available")

    df = pd.DataFrame(benchmark_data)

    if (
        df.empty
        or "target_time" not in df.columns
        or "load_intensity" not in df.columns
    ):
        return create_empty_figure("No valid benchmark data")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["target_time"],
            y=df["load_intensity"],
            mode="lines+markers",
            name="Load Intensity",
            line=dict(color="purple", width=2),
            marker=dict(size=6),
            fill="tozeroy",
            fillcolor="rgba(128, 0, 128, 0.2)",
        )
    )

    fig.update_layout(
        title="Load Intensity Over Time",
        xaxis_title="Target Time (s)",
        yaxis_title="Load Intensity",
        hovermode="x unified",
        height=400,
    )

    return fig


def create_empty_figure(message):
    """Create an empty figure with a message"""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="gray"),
    )
    fig.update_layout(
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        height=400,
    )
    return fig


# ========== CORRELATION TAB CALLBACKS ==========


# Callback to update correlation energy chart
@app.callback(
    Output("correlation-energy-chart", "figure"),
    Input("energy-data-store", "data"),
    Input("correlation-energy-source-radio", "value"),
    Input("hover-position-store", "data"),
)
def update_correlation_energy_chart(energy_data, source, hover_x):
    """Update energy evolution chart in correlation tab"""
    if not energy_data or source not in energy_data:
        return create_empty_figure("No data available")

    data_records = energy_data[source]
    if not data_records:
        return create_empty_figure(f"No {source} data available")

    df = pd.DataFrame(data_records)

    if "elapsed_seconds" not in df.columns:
        return create_empty_figure(f"No elapsed_seconds data available for {source}")

    fig = go.Figure()

    # Create a line for each node
    for node in df["node_name"].unique():
        node_data = df[df["node_name"] == node]
        fig.add_trace(
            go.Scatter(
                x=node_data["elapsed_seconds"],
                y=node_data["energy_value"],
                mode="lines+markers",
                name=node,
                line=dict(width=2),
                marker=dict(size=4),
            )
        )

    fig.update_layout(
        title=f"Energy Evolution ({source.capitalize()})",
        xaxis_title="Time (seconds)",
        yaxis_title="Energy (Watts)" if source == "scaphandre" else "Energy (Joules)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=350,
        uirevision="correlation-energy",  # Preserve UI state including legend clicks
    )

    # Add vertical line if hover position is set
    if hover_x is not None:
        fig.add_vline(
            x=hover_x,
            line_width=2,
            line_dash="dash",
            line_color="red",
            opacity=0.7,
        )

    return fig


# Callback to update correlation transaction status chart
@app.callback(
    Output("correlation-transaction-chart", "figure"),
    Input("benchmark-data-store", "data"),
    Input("hover-position-store", "data"),
)
def update_correlation_transaction_chart(benchmark_data, hover_x):
    """Update transaction status chart in correlation tab"""
    if not benchmark_data:
        return create_empty_figure("No benchmark data available")

    df = pd.DataFrame(benchmark_data)

    if df.empty or "elapsed_seconds" not in df.columns:
        return create_empty_figure("No valid benchmark data")

    fig = go.Figure()

    # Add traces for each transaction type
    if "successful_transactions" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["elapsed_seconds"],
                y=df["successful_transactions"],
                mode="lines+markers",
                name="Successful",
                line=dict(color="green", width=2),
                marker=dict(size=6),
            )
        )

    if "failed_transactions" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["elapsed_seconds"],
                y=df["failed_transactions"],
                mode="lines+markers",
                name="Failed",
                line=dict(color="red", width=2),
                marker=dict(size=6),
            )
        )

    if "dropped_transactions" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["elapsed_seconds"],
                y=df["dropped_transactions"],
                mode="lines+markers",
                name="Dropped",
                line=dict(color="orange", width=2),
                marker=dict(size=6),
            )
        )

    fig.update_layout(
        title="Transaction Status Over Time",
        xaxis_title="Time (seconds)",
        yaxis_title="Number of Transactions",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=350,
        uirevision="correlation-transaction",  # Preserve UI state including legend clicks
    )

    # Add vertical line if hover position is set
    if hover_x is not None:
        fig.add_vline(
            x=hover_x,
            line_width=2,
            line_dash="dash",
            line_color="red",
            opacity=0.7,
        )

    return fig


# Callback to update correlation response time chart
@app.callback(
    Output("correlation-response-time-chart", "figure"),
    Input("benchmark-data-store", "data"),
    Input("hover-position-store", "data"),
)
def update_correlation_response_time_chart(benchmark_data, hover_x):
    """Update average response time chart in correlation tab"""
    if not benchmark_data:
        return create_empty_figure("No benchmark data available")

    df = pd.DataFrame(benchmark_data)

    if (
        df.empty
        or "elapsed_seconds" not in df.columns
        or "avg_response_time" not in df.columns
    ):
        return create_empty_figure("No valid benchmark data")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["elapsed_seconds"],
            y=df["avg_response_time"],
            mode="lines+markers",
            name="Avg Response Time",
            line=dict(color="blue", width=2),
            marker=dict(size=6),
            fill="tozeroy",
            fillcolor="rgba(0, 100, 255, 0.2)",
        )
    )

    fig.update_layout(
        title="Average Response Time",
        xaxis_title="Time (seconds)",
        yaxis_title="Response Time (s)",
        hovermode="x unified",
        height=350,
        uirevision="correlation-response",  # Preserve UI state including legend clicks
    )

    # Add vertical line if hover position is set
    if hover_x is not None:
        fig.add_vline(
            x=hover_x,
            line_width=2,
            line_dash="dash",
            line_color="red",
            opacity=0.7,
        )

    return fig


# Callback to update hover position store based on hover events
@app.callback(
    Output("hover-position-store", "data"),
    Input("correlation-energy-chart", "hoverData"),
    Input("correlation-transaction-chart", "hoverData"),
    Input("correlation-response-time-chart", "hoverData"),
)
def update_hover_position(energy_hover, transaction_hover, response_hover):
    """Update hover position based on any chart hover event"""
    ctx = dash.callback_context

    if not ctx.triggered:
        return None

    # Get which input triggered the callback
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Get hover data from the triggered chart
    hover_data = None
    if trigger_id == "correlation-energy-chart" and energy_hover:
        hover_data = energy_hover
    elif trigger_id == "correlation-transaction-chart" and transaction_hover:
        hover_data = transaction_hover
    elif trigger_id == "correlation-response-time-chart" and response_hover:
        hover_data = response_hover

    # Extract x value from hover data
    if hover_data and "points" in hover_data and len(hover_data["points"]) > 0:
        return hover_data["points"][0]["x"]

    return None


# Callback to update energy profile pie charts by transaction outcome
@app.callback(
    Output("energy-profile-successful-pie", "figure"),
    Output("energy-profile-failed-pie", "figure"),
    Output("energy-profile-dropped-pie", "figure"),
    Input("component-energy-data-store", "data"),
    Input("benchmark-data-store", "data"),
    Input("correlation-energy-source-radio", "value"),
    Input("energy-data-store", "data"),
)
def update_energy_profile_pies(component_data, benchmark_data, source, energy_data):
    """
    Update energy profile pie charts showing component energy distribution
    for successful, failed, and dropped transactions
    """
    # Default empty figures
    empty_fig_successful = create_empty_figure(
        "No data available for successful transactions"
    )
    empty_fig_failed = create_empty_figure("No data available for failed transactions")
    empty_fig_dropped = create_empty_figure(
        "No data available for dropped transactions"
    )

    # Validate inputs
    if not benchmark_data or not component_data:
        return empty_fig_successful, empty_fig_failed, empty_fig_dropped

    # Handle scaphandre case - only ecofloc has component-level data
    if source == "scaphandre":
        return (
            create_empty_figure(
                "Component breakdown only available for Ecofloc source"
            ),
            create_empty_figure(
                "Component breakdown only available for Ecofloc source"
            ),
            create_empty_figure(
                "Component breakdown only available for Ecofloc source"
            ),
        )

    try:
        # Step 1: Load Performance Data and calculate totals
        limbo_df = pd.DataFrame(benchmark_data)

        if limbo_df.empty:
            return empty_fig_successful, empty_fig_failed, empty_fig_dropped

        # Calculate total transactions
        total_successful = (
            limbo_df["successful_transactions"].sum()
            if "successful_transactions" in limbo_df.columns
            else 0
        )
        total_failed = (
            limbo_df["failed_transactions"].sum()
            if "failed_transactions" in limbo_df.columns
            else 0
        )
        total_dropped = (
            limbo_df["dropped_transactions"].sum()
            if "dropped_transactions" in limbo_df.columns
            else 0
        )

        all_transactions = total_successful + total_failed + total_dropped

        # Handle edge case when no transactions
        if all_transactions == 0:
            return (
                create_empty_figure("No transactions recorded"),
                create_empty_figure("No transactions recorded"),
                create_empty_figure("No transactions recorded"),
            )

        # Step 2: Calculate Ratios
        ratio_successful = total_successful / all_transactions
        ratio_failed = total_failed / all_transactions
        ratio_dropped = total_dropped / all_transactions

        # Step 3: Load and Sum Component Energy
        total_cpu_energy = 0
        total_ram_energy = 0
        total_sd_energy = 0
        total_nic_energy = 0

        for component in ["cpu", "ram", "sd", "nic"]:
            if component in component_data and component_data[component]:
                df = pd.DataFrame(component_data[component])
                if not df.empty and "energy_value" in df.columns:
                    total_energy = df["energy_value"].sum()
                    if component == "cpu":
                        total_cpu_energy = total_energy
                    elif component == "ram":
                        total_ram_energy = total_energy
                    elif component == "sd":
                        total_sd_energy = total_energy
                    elif component == "nic":
                        total_nic_energy = total_energy

        # Check if we have any energy data
        total_energy = (
            total_cpu_energy + total_ram_energy + total_sd_energy + total_nic_energy
        )
        if total_energy == 0:
            return (
                create_empty_figure("No energy data available"),
                create_empty_figure("No energy data available"),
                create_empty_figure("No energy data available"),
            )

        # Step 4: Distribute Energy by transaction ratio
        # Successful transactions
        successful_values = [
            total_cpu_energy * ratio_successful,
            total_ram_energy * ratio_successful,
            total_sd_energy * ratio_successful,
            total_nic_energy * ratio_successful,
        ]

        # Failed transactions
        failed_values = [
            total_cpu_energy * ratio_failed,
            total_ram_energy * ratio_failed,
            total_sd_energy * ratio_failed,
            total_nic_energy * ratio_failed,
        ]

        # Dropped transactions
        dropped_values = [
            total_cpu_energy * ratio_dropped,
            total_ram_energy * ratio_dropped,
            total_sd_energy * ratio_dropped,
            total_nic_energy * ratio_dropped,
        ]

        # Component labels
        labels = ["CPU", "RAM", "SD", "NIC"]

        # Step 5: Create Pie Charts
        fig_successful = px.pie(
            values=successful_values,
            names=labels,
            title=f"Energy Profile for Successful Transactions<br>({total_successful:,.0f} transactions, {ratio_successful:.1%})",
            hole=0.3,
        )
        fig_successful.update_traces(textposition="inside", textinfo="percent+label")
        fig_successful.update_layout(height=400)

        fig_failed = px.pie(
            values=failed_values,
            names=labels,
            title=f"Energy Profile for Failed Transactions<br>({total_failed:,.0f} transactions, {ratio_failed:.1%})",
            hole=0.3,
        )
        fig_failed.update_traces(textposition="inside", textinfo="percent+label")
        fig_failed.update_layout(height=400)

        fig_dropped = px.pie(
            values=dropped_values,
            names=labels,
            title=f"Energy Profile for Dropped Transactions<br>({total_dropped:,.0f} transactions, {ratio_dropped:.1%})",
            hole=0.3,
        )
        fig_dropped.update_traces(textposition="inside", textinfo="percent+label")
        fig_dropped.update_layout(height=400)

        return fig_successful, fig_failed, fig_dropped

    except Exception as e:
        error_msg = f"Error creating energy profile pie charts: {str(e)}"
        print(error_msg)
        return (
            create_empty_figure(error_msg),
            create_empty_figure(error_msg),
            create_empty_figure(error_msg),
        )


# ========== AVERAGES TAB CALLBACKS ==========
# NOTE: All callbacks in this section use ECOFLOC data exclusively.
# The data_loader functions (load_ecofloc_data, load_ecofloc_component_data)
# are hardcoded to search only in ecofloc directories, ensuring consistent
# data source regardless of any filters on other tabs.


# Callback to load averages data (all experiments in the selected category)
@app.callback(
    Output("averages-data-store", "data"),
    Input("component-dropdown", "value"),
    Input("intensity-dropdown", "value"),
)
def load_averages_data(component, intensity):
    """
    Load data for all experiments in the selected component/intensity category

    NOTE: This function uses ECOFLOC data exclusively via load_ecofloc_component_data()
    """
    if not component or not intensity:
        return None

    # Get all experiments for this component/intensity combination
    experiments = data_loader.get_available_experiments(component, intensity)

    if not experiments:
        return None

    # Collect data from all experiments
    all_experiments_data = []

    for exp in experiments:
        exp_path = exp["value"]
        exp_name = exp["label"]

        try:
            # Load limbo results to get transaction counts
            limbo_df = data_loader.load_limbo_data(exp_path, intensity)

            if limbo_df.empty:
                continue

            # Calculate total transactions for this experiment
            total_successful = (
                limbo_df["successful_transactions"].sum()
                if "successful_transactions" in limbo_df.columns
                else 0
            )
            total_failed = (
                limbo_df["failed_transactions"].sum()
                if "failed_transactions" in limbo_df.columns
                else 0
            )
            total_dropped = (
                limbo_df["dropped_transactions"].sum()
                if "dropped_transactions" in limbo_df.columns
                else 0
            )

            # Load energy data for all components with node-level detail
            component_energies = {}
            node_component_energies = {}  # Store {node: {component: energy}}

            for comp in ["cpu", "ram", "sd", "nic"]:
                # Use the existing, proven data_loader function
                # NOTE: load_ecofloc_component_data() only reads from ecofloc directories
                comp_df = data_loader.load_ecofloc_component_data(exp_path, comp)

                if not comp_df.empty and "energy_value" in comp_df.columns:
                    # Calculate total energy per node for this component
                    node_totals = comp_df.groupby("node_name")["energy_value"].sum()

                    # Aggregate total for this component across all nodes
                    component_energies[comp] = node_totals.sum()

                    # Store node-level data
                    for node_name, energy in node_totals.items():
                        if node_name not in node_component_energies:
                            node_component_energies[node_name] = {}
                        node_component_energies[node_name][comp] = energy
                else:
                    # No data for this component
                    component_energies[comp] = 0

            # Calculate total energy for this experiment
            total_energy = sum(component_energies.values())

            # Store experiment data
            all_experiments_data.append(
                {
                    "name": exp_name,
                    "path": exp_path,
                    "total_successful": total_successful,
                    "total_failed": total_failed,
                    "total_dropped": total_dropped,
                    "total_energy": total_energy,
                    "component_energies": component_energies,
                    "node_component_energies": node_component_energies,
                }
            )

        except Exception as e:
            print(f"Error loading data for {exp_name}: {e}")
            continue

    if not all_experiments_data:
        return None

    return {
        "component": component,
        "intensity": intensity,
        "experiments": all_experiments_data,
    }


# Callback to display experiment information
@app.callback(
    Output("averages-experiment-info", "children"),
    Input("averages-data-store", "data"),
)
def update_averages_info(averages_data):
    """Display information about experiments in the averages analysis"""
    if not averages_data:
        return html.Div(
            "No data available. Please select a component and intensity.",
            style={"color": "gray"},
        )

    component = averages_data["component"]
    intensity = averages_data["intensity"]
    experiments = averages_data["experiments"]

    num_experiments = len(experiments)

    # Create experiment list
    experiment_names = [exp["name"] for exp in experiments]

    return html.Div(
        [
            html.H4(
                f"Found {num_experiments} experiment{'s' if num_experiments != 1 else ''} for {component}/{intensity}",
                style={"color": "#2c3e50", "marginBottom": 10},
            ),
            html.Div(
                [
                    html.Strong("Experiments in this group:"),
                    html.Ul([html.Li(name) for name in experiment_names]),
                ],
                style={"marginTop": 10},
            ),
        ]
    )


# Callback to create energy profile pie chart by transaction outcome
@app.callback(
    Output("averages-energy-profile-pie", "figure"),
    Input("averages-data-store", "data"),
)
def update_averages_energy_profile(averages_data):
    """
    Create pie chart showing energy distribution by transaction outcome
    across all experiments in the category

    NOTE: Uses ECOFLOC data exclusively (data loaded by load_averages_data callback)
    """
    if not averages_data:
        return create_empty_figure(
            "No data available. Please select a component and intensity."
        )

    experiments = averages_data["experiments"]

    if not experiments:
        return create_empty_figure("No experiments found")

    # Initialize grand totals
    grand_total_success_energy = 0
    grand_total_fail_energy = 0
    grand_total_drop_energy = 0

    # Process each experiment
    for exp in experiments:
        total_successful = exp["total_successful"]
        total_failed = exp["total_failed"]
        total_dropped = exp["total_dropped"]
        total_energy = exp["total_energy"]

        # Calculate total transactions
        total_txns = total_successful + total_failed + total_dropped

        # Apportion energy based on transaction outcome ratios
        if total_txns > 0:
            energy_for_success = total_energy * (total_successful / total_txns)
            energy_for_fail = total_energy * (total_failed / total_txns)
            energy_for_drop = total_energy * (total_dropped / total_txns)
        else:
            energy_for_success = 0
            energy_for_fail = 0
            energy_for_drop = 0

        # Add to grand totals
        grand_total_success_energy += energy_for_success
        grand_total_fail_energy += energy_for_fail
        grand_total_drop_energy += energy_for_drop

    # Create pie chart
    values = [
        grand_total_success_energy,
        grand_total_fail_energy,
        grand_total_drop_energy,
    ]
    names = ["Successful Transactions", "Failed Transactions", "Dropped Transactions"]

    # Check if we have any energy data
    if sum(values) == 0:
        return create_empty_figure("No energy data available")

    # Calculate percentages for label positioning
    total = sum(values)
    percentages = [(v / total) * 100 if total > 0 else 0 for v in values]

    # Determine text positions: small slices (< 4%) go outside, others inside
    text_positions = ["outside" if pct < 4 else "inside" for pct in percentages]

    # Apply static color mapping
    color_map = {
        "Successful Transactions": "green",
        "Failed Transactions": "rgb(168, 37, 37)",
        "Dropped Transactions": "rgb(223, 197, 60)",
    }

    fig = px.pie(
        values=values,
        names=names,
        title="Average Energy Profile by Transaction Outcome",
        hole=0.3,
        color=names,
        color_discrete_map=color_map,
    )

    fig.update_traces(textposition=text_positions, textinfo="percent+label")
    fig.update_layout(height=500)

    return fig


# Callback to create average component energy breakdown bar chart
@app.callback(
    Output("averages-component-breakdown-bar", "figure"),
    Input("averages-data-store", "data"),
)
def update_averages_component_breakdown(averages_data):
    """
    Create grouped bar chart showing average energy consumption of each
    hardware component by node across all experiments in the category

    NOTE: Uses ECOFLOC data exclusively (data loaded by load_averages_data callback)
    """
    # print(
    #     f"DEBUG: update_averages_component_breakdown called with averages_data: {averages_data is not None}"
    # )

    if not averages_data:
        return create_empty_figure(
            "No data available. Please select a component and intensity."
        )

    experiments = averages_data["experiments"]
    # print(
    #     f"DEBUG: Averaging data for experiments: {[exp['path'] for exp in experiments]}"
    # )

    if not experiments:
        return create_empty_figure("No experiments found")

    # Collect all node-component energy data across all experiments
    # Structure: {node: {component: [list of energies from each experiment]}}
    node_component_data = {}

    for exp in experiments:
        # print(f"DEBUG: Processing experiment: {exp['path']}")
        node_energies = exp.get("node_component_energies", {})
        # print(f"DEBUG:   - node_component_energies: {node_energies}")

        for node_name, components in node_energies.items():
            if node_name not in node_component_data:
                node_component_data[node_name] = {
                    "cpu": [],
                    "ram": [],
                    "sd": [],
                    "nic": [],
                }

            for component in ["cpu", "ram", "sd", "nic"]:
                energy = components.get(component, 0)
                # print(f"  - Reading component: {component} for node {node_name}")
                # print(f"    - Calculated Energy: {energy} J")
                node_component_data[node_name][component].append(energy)

    # Calculate averages for each node-component pair
    averaged_data = []

    for node_name, components in node_component_data.items():
        for component in ["cpu", "ram", "sd", "nic"]:
            energies = components[component]
            if energies:
                avg_energy = sum(energies) / len(energies)
                averaged_data.append(
                    {
                        "node_name": node_name,
                        "component": component.upper(),
                        "average_energy_joules": avg_energy,
                    }
                )

    if not averaged_data:
        return create_empty_figure("No component energy data available")

    # Create DataFrame for plotting
    df = pd.DataFrame(averaged_data)
    # print(f"DEBUG: Final DataFrame for chart:\n{df.to_string()}")

    # Apply static color mapping
    color_map = {
        "CPU": "rgb(168, 37, 37)",
        "RAM": "rgb(21, 11, 147)",
        "SD": "rgb(223, 197, 60)",
        "NIC": "purple",
    }

    # Create grouped bar chart
    fig = px.bar(
        df,
        x="node_name",
        y="average_energy_joules",
        color="component",
        barmode="group",
        title="Average Component Energy Breakdown by Node",
        labels={
            "node_name": "Node",
            "average_energy_joules": "Average Energy (Joules)",
            "component": "Component",
        },
        color_discrete_map=color_map,
    )

    fig.update_layout(
        height=500,
        xaxis_title="Node",
        yaxis_title="Average Energy (Joules)",
        legend_title="Component",
        hovermode="x unified",
    )

    return fig


# Callback to create average overall energy evolution chart
@app.callback(
    Output("averages-overall-energy-evolution", "figure"),
    Input("component-dropdown", "value"),
    Input("intensity-dropdown", "value"),
)
def update_averages_overall_energy_evolution(component, intensity):
    """
    Create line chart showing average total energy over time
    across all experiments in the selected category

    NOTE: Uses ECOFLOC data exclusively via load_ecofloc_data()
    """
    if not component or not intensity:
        return create_empty_figure(
            "No data available. Please select a component and intensity."
        )

    # Get all experiments for this component/intensity combination
    experiments = data_loader.get_available_experiments(component, intensity)

    if not experiments:
        return create_empty_figure("No experiments found")

    # Collect time-series data from all experiments
    all_time_series = []

    for exp in experiments:
        exp_path = exp["value"]

        try:
            # Load ecofloc data for unified component view
            # NOTE: load_ecofloc_data() only reads from ecofloc directories
            ecofloc_df = data_loader.load_ecofloc_data(exp_path, component)

            if ecofloc_df.empty or "elapsed_seconds" not in ecofloc_df.columns:
                continue

            # Aggregate total energy across all nodes at each time point
            time_series = (
                ecofloc_df.groupby("elapsed_seconds")["energy_value"]
                .sum()
                .reset_index()
            )
            time_series["experiment"] = exp["label"]

            all_time_series.append(time_series)

        except Exception as e:
            print(f"Error loading data for {exp['label']}: {e}")
            continue

    if not all_time_series:
        return create_empty_figure("No valid energy data available")

    # Combine all time series and calculate average
    combined_df = pd.concat(all_time_series, ignore_index=True)

    # Calculate average energy at each elapsed_seconds point
    avg_time_series = (
        combined_df.groupby("elapsed_seconds")["energy_value"].mean().reset_index()
    )

    # Create line chart
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=avg_time_series["elapsed_seconds"],
            y=avg_time_series["energy_value"],
            mode="lines+markers",
            name="Average Total Energy",
            line=dict(width=3, color="blue"),
            marker=dict(size=5),
        )
    )

    fig.update_layout(
        title=f"Average Overall Energy Evolution ({component.upper()}/{intensity.upper()})",
        xaxis_title="Time (seconds)",
        yaxis_title="Average Energy (Joules)",
        hovermode="x unified",
        height=500,
    )

    return fig


# Callback to create average CPU energy evolution chart
@app.callback(
    Output("averages-cpu-energy-evolution", "figure"),
    Input("component-dropdown", "value"),
    Input("intensity-dropdown", "value"),
)
def update_averages_cpu_energy_evolution(component, intensity):
    """
    Create line chart showing average CPU energy over time

    NOTE: Uses ECOFLOC data exclusively via create_component_average_chart()
    """
    return create_component_average_chart(component, intensity, "cpu", "CPU")


# Callback to create average RAM energy evolution chart
@app.callback(
    Output("averages-ram-energy-evolution", "figure"),
    Input("component-dropdown", "value"),
    Input("intensity-dropdown", "value"),
)
def update_averages_ram_energy_evolution(component, intensity):
    """
    Create line chart showing average RAM energy over time

    NOTE: Uses ECOFLOC data exclusively via create_component_average_chart()
    """
    return create_component_average_chart(component, intensity, "ram", "RAM")


# Callback to create average SD energy evolution chart
@app.callback(
    Output("averages-sd-energy-evolution", "figure"),
    Input("component-dropdown", "value"),
    Input("intensity-dropdown", "value"),
)
def update_averages_sd_energy_evolution(component, intensity):
    """
    Create line chart showing average SD energy over time

    NOTE: Uses ECOFLOC data exclusively via create_component_average_chart()
    """
    return create_component_average_chart(component, intensity, "sd", "SD")


# Callback to create average NIC energy evolution chart
@app.callback(
    Output("averages-nic-energy-evolution", "figure"),
    Input("component-dropdown", "value"),
    Input("intensity-dropdown", "value"),
)
def update_averages_nic_energy_evolution(component, intensity):
    """
    Create line chart showing average NIC energy over time

    NOTE: Uses ECOFLOC data exclusively via create_component_average_chart()
    """
    return create_component_average_chart(component, intensity, "nic", "NIC")


def create_component_average_chart(component, intensity, target_component, label):
    """
    Helper function to create average energy evolution chart for a specific component

    Args:
        component: Selected component filter (cpu, ram, sd, nic, unified)
        intensity: Selected intensity filter (low, med, high)
        target_component: The specific hardware component to chart (cpu, ram, sd, nic)
        label: Display label for the component (CPU, RAM, SD, NIC)

    Returns:
        Plotly figure showing average energy evolution

    NOTE: This function uses ECOFLOC data exclusively via load_ecofloc_component_data()
    """
    if not component or not intensity:
        return create_empty_figure(
            "No data available. Please select a component and intensity."
        )

    # Get all experiments for this component/intensity combination
    experiments = data_loader.get_available_experiments(component, intensity)

    if not experiments:
        return create_empty_figure("No experiments found")

    # Collect time-series data from all experiments
    all_time_series = []

    for exp in experiments:
        exp_path = exp["value"]

        try:
            # Load component-specific data
            # NOTE: load_ecofloc_component_data() only reads from ecofloc directories
            comp_df = data_loader.load_ecofloc_component_data(exp_path, target_component)

            if comp_df.empty or "elapsed_seconds" not in comp_df.columns:
                continue

            # Aggregate total energy across all nodes at each time point
            time_series = (
                comp_df.groupby("elapsed_seconds")["energy_value"]
                .sum()
                .reset_index()
            )
            time_series["experiment"] = exp["label"]

            all_time_series.append(time_series)

        except Exception as e:
            print(f"Error loading {target_component} data for {exp['label']}: {e}")
            continue

    if not all_time_series:
        return create_empty_figure(f"No valid {label} energy data available")

    # Combine all time series and calculate average
    combined_df = pd.concat(all_time_series, ignore_index=True)

    # Calculate average energy at each elapsed_seconds point
    avg_time_series = (
        combined_df.groupby("elapsed_seconds")["energy_value"].mean().reset_index()
    )

    # Create line chart
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=avg_time_series["elapsed_seconds"],
            y=avg_time_series["energy_value"],
            mode="lines+markers",
            name=f"Average {label} Energy",
            line=dict(width=3),
            marker=dict(size=5),
        )
    )

    fig.update_layout(
        title=f"Average {label} Energy Evolution ({component.upper()}/{intensity.upper()})",
        xaxis_title="Time (seconds)",
        yaxis_title="Average Energy (Joules)",
        hovermode="x unified",
        height=400,
    )

    return fig


if __name__ == "__main__":
    print("Starting Dash application...")
    print("Access the dashboard at: http://127.0.0.1:8050")
    app.run(debug=True, host="0.0.0.0", port=8050)
