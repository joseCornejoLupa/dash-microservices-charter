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
                                # Energy charts
                                html.Div(
                                    [
                                        dcc.Graph(id="energy-evolution-chart"),
                                    ]
                                ),
                                # Component-specific energy charts
                                html.Div(
                                    [
                                        html.H4(
                                            "Component-Level Energy Analysis",
                                            style={"color": "#34495e", "marginTop": 30, "marginBottom": 20},
                                        ),
                                        dcc.Graph(id="cpu-energy-chart"),
                                        dcc.Graph(id="ram-energy-chart"),
                                        dcc.Graph(id="sd-energy-chart"),
                                        dcc.Graph(id="nic-energy-chart"),
                                    ],
                                    style={"marginTop": 20},
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                dcc.Graph(
                                                    id="energy-distribution-chart"
                                                ),
                                            ],
                                            style={
                                                "width": "48%",
                                                "display": "inline-block",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                dcc.Graph(id="cumulative-energy-chart"),
                                            ],
                                            style={
                                                "width": "48%",
                                                "display": "inline-block",
                                                "float": "right",
                                            },
                                        ),
                                    ]
                                ),
                                # Process-level energy treemap
                                html.Div(
                                    [
                                        dcc.Graph(id="process-energy-treemap"),
                                    ],
                                    style={"marginTop": 20},
                                ),
                                # Node selector for process-level time-series
                                html.Div(
                                    [
                                        html.Label(
                                            "Select Node to Inspect:",
                                            style={
                                                "fontWeight": "bold",
                                                "marginRight": 10,
                                            },
                                        ),
                                        dcc.Dropdown(
                                            id="node-selector-dropdown",
                                            options=[],
                                            placeholder="Select a node",
                                            style={"width": "300px"},
                                        ),
                                    ],
                                    style={"marginTop": 20, "marginBottom": 10},
                                ),
                                # Process-level energy time-series chart
                                html.Div(
                                    [
                                        dcc.Graph(id="process-energy-timeseries"),
                                    ],
                                    style={"marginTop": 10},
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
                # Tab 3: Correlation
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
    if component == 'unified':
        options = [
            {"label": "LOW", "value": "low"},
            {"label": "MED", "value": "med"},
            {"label": "HIGH", "value": "high"},
            {"label": "SPECIFIC-SCENARIOS", "value": "specific-scenarios"}
        ]
        return options, None

    # For other components, use the standard intensities from data_loader
    intensities = data_loader.get_available_intensities(component)
    options = [{"label": i.upper(), "value": i} for i in intensities]
    return options, None


# Callback to populate experiment dropdown based on component and intensity
@app.callback(
    Output("experiment-dropdown", "options"),
    Output("experiment-dropdown", "value"),
    Input("component-dropdown", "value"),
    Input("intensity-dropdown", "value"),
)
def populate_experiments(component, intensity):
    """Populate experiment dropdown based on component and intensity"""
    if not component or not intensity:
        return [], None

    experiments = data_loader.get_available_experiments(component, intensity)
    return experiments, None


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
    for component in ['cpu', 'ram', 'sd', 'nic']:
        df = data_loader.load_ecofloc_component_data(experiment_path, component)
        component_data[component] = df.to_dict('records') if not df.empty else []

    return component_data


# Callback to update CPU energy chart
@app.callback(
    Output("cpu-energy-chart", "figure"),
    Input("component-energy-data-store", "data"),
)
def update_cpu_energy_chart(component_data):
    """Update CPU energy evolution time-series chart"""
    if not component_data or 'cpu' not in component_data:
        return create_empty_figure("No CPU data available")

    data_records = component_data['cpu']
    if not data_records:
        return create_empty_figure("No CPU data available")

    df = pd.DataFrame(data_records)

    if 'elapsed_seconds' not in df.columns or df.empty:
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
    if not component_data or 'ram' not in component_data:
        return create_empty_figure("No RAM data available")

    data_records = component_data['ram']
    if not data_records:
        return create_empty_figure("No RAM data available")

    df = pd.DataFrame(data_records)

    if 'elapsed_seconds' not in df.columns or df.empty:
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
    if not component_data or 'sd' not in component_data:
        return create_empty_figure("No SD data available")

    data_records = component_data['sd']
    if not data_records:
        return create_empty_figure("No SD data available")

    df = pd.DataFrame(data_records)

    if 'elapsed_seconds' not in df.columns or df.empty:
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
    if not component_data or 'nic' not in component_data:
        return create_empty_figure("No NIC data available")

    data_records = component_data['nic']
    if not data_records:
        return create_empty_figure("No NIC data available")

    df = pd.DataFrame(data_records)

    if 'elapsed_seconds' not in df.columns or df.empty:
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
            if 'elapsed_seconds' in df_eco.columns:
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
            if 'elapsed_seconds' in df_scaph.columns:
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
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
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
    if 'elapsed_seconds' not in df.columns:
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
                pids_df,
                on=['node_name', 'pid'],
                how='inner'
            )

            if not merged_df.empty:
                # Calculate process-level energy per node
                process_energy = merged_df.groupby(['node_name', 'name_pid'])['energy_value'].sum().reset_index()

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
                    subplot_titles=["Energy Distribution by Node"] + [f"Process Distribution on {node}" for node in nodes]
                )

                # Add main pie chart (node distribution)
                fig.add_trace(
                    go.Pie(
                        labels=energy_by_node["node_name"],
                        values=energy_by_node["energy_value"],
                        name="Node Distribution",
                        hole=0.3,
                        textposition="inside",
                        textinfo="percent+label"
                    ),
                    row=1,
                    col=1
                )

                # Add per-node process distribution pie charts
                for idx, node in enumerate(nodes):
                    node_process_data = process_energy[process_energy['node_name'] == node]

                    # Calculate position in grid
                    chart_idx = idx + 2  # +2 because idx starts at 0 and main chart is at 1
                    row = (chart_idx - 1) // cols + 1
                    col = (chart_idx - 1) % cols + 1

                    fig.add_trace(
                        go.Pie(
                            labels=node_process_data["name_pid"],
                            values=node_process_data["energy_value"],
                            name=f"{node} Processes",
                            hole=0.3,
                            textposition="inside",
                            textinfo="percent+label"
                        ),
                        row=row,
                        col=col
                    )

                # Calculate appropriate height based on rows
                height = max(400, rows * 300)

                fig.update_layout(
                    height=height,
                    showlegend=False,
                    title_text="Energy Distribution Analysis"
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
        return create_empty_figure("Component breakdown only available for Ecofloc source")

    # Gather all nodes from component data
    all_nodes = set()
    component_dfs = {}

    for component in ['cpu', 'ram', 'sd', 'nic']:
        if component in component_data and component_data[component]:
            df = pd.DataFrame(component_data[component])
            if not df.empty and 'node_name' in df.columns:
                component_dfs[component] = df
                all_nodes.update(df['node_name'].unique())

    if not all_nodes:
        return create_empty_figure("No component data available")

    nodes = sorted(list(all_nodes))
    num_nodes = len(nodes)

    # Create subplots - one bar chart per node
    fig = make_subplots(
        rows=num_nodes,
        cols=1,
        subplot_titles=[f"Component Energy on {node}" for node in nodes],
        vertical_spacing=0.15 / max(num_nodes, 1)
    )

    # For each node, create a horizontal bar chart showing component breakdown
    for idx, node in enumerate(nodes):
        component_energies = []
        component_names = []

        for component in ['cpu', 'ram', 'sd', 'nic']:
            if component in component_dfs:
                node_data = component_dfs[component][component_dfs[component]['node_name'] == node]
                total_energy = node_data['energy_value'].sum() if not node_data.empty else 0
                component_energies.append(total_energy)
                component_names.append(component.upper())
            else:
                component_energies.append(0)
                component_names.append(component.upper())

        fig.add_trace(
            go.Bar(
                x=component_energies,
                y=component_names,
                orientation='h',
                name=node,
                showlegend=False,
                marker=dict(
                    color=component_energies,
                    colorscale='Viridis',
                ),
                text=[f"{e:.2f}" for e in component_energies],
                textposition='auto',
            ),
            row=idx + 1,
            col=1
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
        height=height,
        title_text="Component Energy Breakdown by Node",
        showlegend=False
    )

    return fig


# Callback to update process energy treemap
@app.callback(
    Output("process-energy-treemap", "figure"),
    Input("energy-data-store", "data"),
    Input("energy-source-radio", "value"),
    Input("experiment-dropdown", "value"),
    State("current-component-store", "data"),
)
def update_process_energy_treemap(energy_data, source, experiment_path, component):
    """Update process-level energy consumption treemap"""
    if not energy_data or not experiment_path or not component:
        return create_empty_figure("No data available")

    # Only use ecofloc for PID-level data (scaphandre doesn't have PID data)
    if source == "scaphandre":
        return create_empty_figure("Process-level energy data only available for Ecofloc source")

    if source == "both":
        # Use ecofloc data when "both" is selected
        source = "ecofloc"

    try:
        # Load informe_pids.csv
        pids_df = data_loader.load_informe_pids(experiment_path)

        if pids_df.empty:
            return create_empty_figure("No process information available (informe_pids.csv not found)")

        # Load per-PID energy data
        pid_energy_df = data_loader.load_ecofloc_pid_data(experiment_path, component)

        if pid_energy_df.empty:
            return create_empty_figure("No per-PID energy data available")

        # Merge PID data with process names
        merged_df = pid_energy_df.merge(
            pids_df,
            on=['node_name', 'pid'],
            how='inner'
        )

        if merged_df.empty:
            return create_empty_figure("No matching process data found")

        # Aggregate total energy by node and process
        aggregated = merged_df.groupby(['node_name', 'name_pid'])['energy_value'].sum().reset_index()
        aggregated = aggregated.sort_values('energy_value', ascending=False)

        # Create treemap
        fig = px.treemap(
            aggregated,
            path=[px.Constant("All Nodes"), 'node_name', 'name_pid'],
            values='energy_value',
            title="Process Energy Consumption Breakdown",
            color='energy_value',
            color_continuous_scale='Viridis',
            hover_data={'energy_value': ':.2f'}
        )

        fig.update_traces(
            textinfo="label+value",
            textposition="middle center",
        )

        fig.update_layout(
            height=500,
            margin=dict(t=50, l=25, r=25, b=25)
        )

        return fig

    except Exception as e:
        return create_empty_figure(f"Error creating treemap: {str(e)}")


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
        unique_nodes = sorted(pids_df['node_name'].unique())
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
            return create_empty_figure("No process information available (informe_pids.csv not found)")

        # Load per-PID energy data
        pid_energy_df = data_loader.load_ecofloc_pid_data(experiment_path, component)

        if pid_energy_df.empty:
            return create_empty_figure("No per-PID energy data available")

        # Merge PID data with process names
        merged_df = pid_energy_df.merge(
            pids_df,
            on=['node_name', 'pid'],
            how='inner'
        )

        if merged_df.empty:
            return create_empty_figure("No matching process data found")

        # Filter data for selected node
        node_data = merged_df[merged_df['node_name'] == selected_node]

        if node_data.empty:
            return create_empty_figure(f"No data available for node: {selected_node}")

        # Calculate elapsed seconds from first timestamp
        min_timestamp = node_data['timestamp'].min()
        node_data = node_data.copy()
        node_data['elapsed_seconds'] = (node_data['timestamp'] - min_timestamp).dt.total_seconds()

        # Create time-series chart with a line for each process
        fig = go.Figure()

        # Get unique processes for this node
        unique_processes = node_data['name_pid'].unique()

        for process_name in unique_processes:
            process_data = node_data[node_data['name_pid'] == process_name]

            fig.add_trace(
                go.Scatter(
                    x=process_data['elapsed_seconds'],
                    y=process_data['energy_value'],
                    mode='lines+markers',
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
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
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

    if 'elapsed_seconds' not in df.columns:
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
        uirevision='correlation-energy',  # Preserve UI state including legend clicks
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
        uirevision='correlation-transaction',  # Preserve UI state including legend clicks
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
        uirevision='correlation-response',  # Preserve UI state including legend clicks
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


if __name__ == "__main__":
    print("Starting Dash application...")
    print("Access the dashboard at: http://127.0.0.1:8050")
    app.run(debug=True, host="0.0.0.0", port=8050)
