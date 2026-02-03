import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from data_loader import DataLoader

# App Configuration
app = dash.Dash(__name__)
app.title = "Full Benchmark & Energy Analysis"

# Initialize Data Loader
ROOT_DIR = "/home/luish/Documents/death/dash-microservices-charter"
data_loader = DataLoader(ROOT_DIR)

# --- HELPER FUNCTIONS ---

def create_empty_figure(title="No data available"):
    """Create an empty figure with a title"""
    return go.Figure().update_layout(title=title, template="plotly_white")

def create_dashboard_grid(prefix):
    """Genera la estructura HTML de los gráficos con un prefijo único para los IDs"""
    return html.Div([
        # --- Energy Section (Ecofloc) ---
        html.H3("Ecofloc Energy Consumption Analysis", style={"textAlign": "center", "color": "#7f8c8d", "marginTop": "20px"}),
        html.Div([
            dcc.Graph(id=f"{prefix}-absolute-energy-chart")
        ], style={"marginBottom": "20px", "boxShadow": "0 1px 3px rgba(0,0,0,0.12)", "padding": "10px", "borderRadius": "5px", "backgroundColor": "white"}),
        # --- Scaphandre Section (New) ---
        html.H3("Scaphandre Power Analysis (Global/CPU)", style={"textAlign": "center", "color": "#e67e22", "marginTop": "20px"}),
        html.Div([
            dcc.Graph(id=f"{prefix}-scaphandre-chart")
        ], style={"marginBottom": "50px", "boxShadow": "0 1px 3px rgba(0,0,0,0.12)", "padding": "10px", "borderRadius": "5px", "backgroundColor": "white"}),
        html.Div([
            dcc.Graph(id=f"{prefix}-normalized-energy-chart")
        ], style={"marginBottom": "30px", "boxShadow": "0 1px 3px rgba(0,0,0,0.12)", "padding": "10px", "borderRadius": "5px", "backgroundColor": "white"}),


        # --- Benchmark Section ---
        html.H3("Average Benchmark Metrics", style={"textAlign": "center", "color": "#7f8c8d", "marginBottom": "20px"}),
        html.Div([
            html.Div([
                html.Div([dcc.Graph(id=f"{prefix}-load-chart")], style={"width": "32%", "display": "inline-block", "marginRight": "1%"}),
                html.Div([dcc.Graph(id=f"{prefix}-success-chart")], style={"width": "32%", "display": "inline-block", "marginRight": "1%"}),
                html.Div([dcc.Graph(id=f"{prefix}-failed-chart")], style={"width": "32%", "display": "inline-block"}),
            ], style={"marginBottom": "20px"}),
            html.Div([
                html.Div([dcc.Graph(id=f"{prefix}-dropped-chart")], style={"width": "32%", "display": "inline-block", "marginRight": "1%"}),
                html.Div([dcc.Graph(id=f"{prefix}-response-chart")], style={"width": "32%", "display": "inline-block", "marginRight": "1%"}),
                html.Div([dcc.Graph(id=f"{prefix}-dispatch-chart")], style={"width": "32%", "display": "inline-block"}),
            ]),
        ], style={"width": "100%", "marginBottom": "50px"}),
        
        # Badge for info
        html.Div(id=f"{prefix}-badge", style={"textAlign": "center", "color": "#2980b9", "fontWeight": "bold", "fontSize": "16px", "marginTop": "20px"})
    ])

def generate_figures_from_experiments(experiments, intensity_label):
    """Lógica central para procesar datos y generar figuras Plotly"""
    empty = go.Figure().update_layout(title="No data available", template="plotly_white")
    
    if not experiments:
        # Retornamos empty para Ecofloc(2) + Scaphandre(1) + Benchmark(6) + Badge(1) = 10 outputs
        return [empty]*9 + ["No experiments found"]

    # --- 1. Process Ecofloc Energy ---
    node_comp_data = []
    
    # --- 2. Process Scaphandre Energy ---
    scap_node_data = []

    for exp in experiments:
        path = exp['value']
        
        # A. Ecofloc Data
        for comp_type in ['cpu', 'ram', 'sd', 'nic']:
            df_comp = data_loader.load_ecofloc_component_data(path, comp_type)
            if not df_comp.empty:
                totals = df_comp.groupby('node_name')['energy_value'].sum().reset_index()
                totals['component'] = comp_type.upper()
                node_comp_data.append(totals)
        
        # B. Scaphandre Data
        df_scap = data_loader.load_scaphandre_data(path)
        if not df_scap.empty:
            # Scaphandre results: Sum energy value per node for this experiment
            totals_scap = df_scap.groupby('node_name')['energy_value'].sum().reset_index()
            scap_node_data.append(totals_scap)

    # --- Generate Ecofloc Charts ---
    if not node_comp_data:
         fig_abs = empty
         fig_norm = empty
    else:
        full_energy_df = pd.concat(node_comp_data)
        avg_energy = full_energy_df.groupby(['node_name', 'component'])['energy_value'].mean().reset_index()

        # Absoluto
        fig_abs = px.bar(
            avg_energy, x="node_name", y="energy_value", color="component", barmode="group",
            title=f"Ecofloc: Absolute Average Energy - Joules ({intensity_label})",
            labels={"energy_value": "Energy (Joules)", "node_name": "Node"},
            text_auto='.1f'
        )
        fig_abs.update_layout(template="plotly_white", height=400)

        # Normalizado
        max_val = avg_energy['energy_value'].max()
        min_val = avg_energy['energy_value'].min()
        denominator = (max_val - min_val) if max_val > min_val else 1
        avg_energy['energy_normalized'] = (avg_energy['energy_value'] - min_val) / denominator

        fig_norm = px.bar(
            avg_energy, x="node_name", y="energy_normalized", color="component", barmode="group",
            title=f"Ecofloc: Normalized Average Energy ({intensity_label})",
            labels={"energy_normalized": "Norm. Energy", "node_name": "Node"},
            text_auto='.2f'
        )
        fig_norm.update_layout(template="plotly_white", height=400)

    # --- Generate Scaphandre Chart ---
    if not scap_node_data:
        fig_scap = empty.update_layout(title="No Scaphandre data available")
    else:
        full_scap_df = pd.concat(scap_node_data)
        # Promedio por nodo a través de los experimentos
        avg_scap = full_scap_df.groupby('node_name')['energy_value'].mean().reset_index()
        
        fig_scap = px.bar(
            avg_scap, x="node_name", y="energy_value",
            title=f"Scaphandre: Average Energy Consumption (Global/CPU) - ({intensity_label})",
            labels={"energy_value": "Average Energy (Joules/Watts)", "node_name": "Node"},
            text_auto='.1f',
            color_discrete_sequence=['#e67e22'] # Color naranja distintivo para Scaphandre
        )
        fig_scap.update_layout(template="plotly_white", height=400)


    # --- 3. Process Benchmarks ---
    benchmark_list = []
    for exp in experiments:
        path = exp['value']
        # Try to infer intensity or iterate standard ones
        for possible_int in ['low', 'med', 'high', 'specific-scenarios']:
            df = data_loader.load_limbo_data(path, possible_int)
            if not df.empty:
                benchmark_list.append(df)
                break 

    if not benchmark_list:
        return [fig_abs, fig_norm, fig_scap] + [empty]*6 + ["No benchmark data found"]

    full_bench_df = pd.concat(benchmark_list)
    avg_bench = full_bench_df.groupby('target_time')[[
        'load_intensity', 'successful_transactions', 'failed_transactions', 
        'dropped_transactions', 'avg_response_time', 'final_batch_dispatch_time'
    ]].mean().reset_index()

    def create_chart(y_col, title, color, y_label):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=avg_bench['target_time'], y=avg_bench[y_col], mode='lines', name=title,
            line=dict(color=color, width=2), fill='tozeroy',
            fillcolor=f"rgba{color.replace('rgb', '').replace(')', ', 0.1)')}" if 'rgb' in color else color
        ))
        fig.update_layout(title=title, xaxis_title="Time (s)", yaxis_title=y_label, template="plotly_white", height=300, margin=dict(l=40, r=20, t=40, b=40), showlegend=False)
        return fig

    figs = [
        create_chart('load_intensity', "Load Intensity", "purple", "Intensity"),
        create_chart('successful_transactions', "Successful Tx", "rgb(46, 204, 113)", "Requests (n)"),
        create_chart('failed_transactions', "Failed Tx", "rgb(231, 76, 60)", "Requests (n)"),
        create_chart('dropped_transactions', "Dropped Tx", "rgb(243, 156, 18)", "Requests (n)"),
        create_chart('avg_response_time', "Avg Response Time", "rgb(52, 152, 219)", "Response Time (s)"),
        create_chart('final_batch_dispatch_time', "Batch Dispatch Time", "rgb(155, 89, 182)", "Dispatch Time (s)")
    ]
    
    badge_text = f"Analysis based on {len(experiments)} experiments ({intensity_label})"
    
    # Return order: Ecofloc Abs, Ecofloc Norm, Scaphandre, Benchmarks(6), Badge
    return [fig_abs, fig_norm, fig_scap] + figs + [badge_text]


def generate_granular_all_experiments(component, intensity, selected_node, filter_type, energy_source):
    """Generate granular analysis for ALL experiments (average components + average intensities)"""
    try:
        # Collect all experiments
        all_experiments = []
        components_to_use = ['cpu', 'ram', 'nic', 'sd'] if component == 'average' else [component]
        
        for comp in components_to_use:
            intensities_to_use = data_loader.get_available_intensities(comp) if intensity == 'average' else [intensity]
            for intens in intensities_to_use:
                all_experiments.extend(data_loader.get_available_experiments(comp, intens))
        
        # Remove duplicates
        unique_experiments = list({exp['value']: exp for exp in all_experiments}.values())
        
        if not unique_experiments:
            empty = create_empty_figure("No experiments found")
            return [empty]*6 + ["No experiments found for the selected criteria."]
        
        # Aggregate data from all experiments
        all_energy_data = []
        all_benchmark_data = []
        all_scap_data = []
        
        for exp in unique_experiments:
            exp_path = exp['value']
            
            # Load energy data
            if energy_source == "ecofloc":
                for comp_type in ['cpu', 'ram', 'sd', 'nic']:
                    df = data_loader.load_ecofloc_component_data(exp_path, comp_type)
                    if not df.empty:
                        df['component'] = comp_type.upper()
                        all_energy_data.append(df)
            else:
                df = data_loader.load_scaphandre_data(exp_path)
                if not df.empty:
                    all_scap_data.append(df)
            
            # Load benchmark data
            for intens in ['low', 'med', 'high', 'specific-scenarios']:
                df = data_loader.load_limbo_data(exp_path, intens)
                if not df.empty:
                    all_benchmark_data.append(df)
                    break
        
        # --- 1. Energy by Node ---
        if energy_source == "ecofloc" and all_energy_data:
            combined_energy = pd.concat(all_energy_data)
            
            if selected_node and selected_node != "all":
                combined_energy = combined_energy[combined_energy['node_name'] == selected_node]
            
            # Average by node and component
            avg_energy = combined_energy.groupby(['node_name', 'component'])['energy_value'].mean().reset_index()
            
            fig_energy_node = px.bar(
                avg_energy, x="node_name", y="energy_value", color="component",
                barmode="group", title=f"Average Energy by Node ({len(unique_experiments)} experiments)",
                labels={"energy_value": "Energy (Joules)", "node_name": "Node"}
            )
            
            # Energy by component (pie)
            comp_totals = avg_energy.groupby('component')['energy_value'].sum().reset_index()
            fig_energy_comp = px.pie(
                comp_totals, values="energy_value", names="component",
                title="Average Energy Distribution by Component", hole=0.4
            )
        elif energy_source == "scaphandre" and all_scap_data:
            combined_scap = pd.concat(all_scap_data)
            
            if selected_node and selected_node != "all":
                combined_scap = combined_scap[combined_scap['node_name'] == selected_node]
            
            avg_scap = combined_scap.groupby('node_name')['energy_value'].mean().reset_index()
            
            fig_energy_node = px.bar(
                avg_scap, x="node_name", y="energy_value",
                title=f"Average Energy by Node (Scaphandre, {len(unique_experiments)} experiments)",
                labels={"energy_value": "Energy (Joules)", "node_name": "Node"},
                color_discrete_sequence=['#e67e22']
            )
            fig_energy_comp = create_empty_figure("Component breakdown only available for Ecofloc")
        else:
            fig_energy_node = create_empty_figure("No energy data available")
            fig_energy_comp = create_empty_figure("No energy data available")
        
        # --- 2. Transaction Breakdown ---
        if all_benchmark_data:
            combined_bench = pd.concat(all_benchmark_data)
            
            total_success = combined_bench.get('successful_transactions', pd.Series([0])).sum()
            total_failed = combined_bench.get('failed_transactions', pd.Series([0])).sum()
            total_dropped = combined_bench.get('dropped_transactions', pd.Series([0])).sum()
            
            fig_transactions = px.pie(
                values=[total_success, total_failed, total_dropped],
                names=["Successful", "Failed", "Dropped"],
                title=f"Transaction Breakdown ({len(unique_experiments)} experiments)",
                color_discrete_map={"Successful": "green", "Failed": "red", "Dropped": "orange"}
            )
            
            # Response time distribution
            if 'avg_response_time' in combined_bench.columns:
                fig_response = px.histogram(
                    combined_bench, x="avg_response_time", nbins=30,
                    title="Response Time Distribution (All Experiments)",
                    labels={"avg_response_time": "Response Time (s)", "count": "Frequency"}
                )
            else:
                fig_response = create_empty_figure("No response time data")
        else:
            fig_transactions = create_empty_figure("No benchmark data available")
            fig_response = create_empty_figure("No response time data")
        
        # --- 3. Process and Timeline (simplified for all experiments) ---
        fig_process = create_empty_figure("Process analysis not available for aggregated view")
        
        # Energy timeline (average across experiments)
        if energy_source == "ecofloc" and all_energy_data:
            combined_energy = pd.concat(all_energy_data)
            if 'elapsed_seconds' in combined_energy.columns:
                # Group by time buckets and average
                combined_energy['time_bucket'] = (combined_energy['elapsed_seconds'] // 10) * 10
                timeline_avg = combined_energy.groupby('time_bucket')['energy_value'].mean().reset_index()
                
                fig_timeline = go.Figure()
                fig_timeline.add_trace(go.Scatter(
                    x=timeline_avg['time_bucket'],
                    y=timeline_avg['energy_value'],
                    mode='lines+markers',
                    name='Average Energy',
                    line=dict(width=2, color='#3498db'),
                    marker=dict(size=4)
                ))
                fig_timeline.update_layout(
                    title="Average Energy Timeline (All Experiments)",
                    xaxis_title="Time (seconds)",
                    yaxis_title="Energy (Joules)",
                    template="plotly_white"
                )
            else:
                fig_timeline = create_empty_figure("No timeline data available")
        else:
            fig_timeline = create_empty_figure("Timeline not available for current selection")
        
        # --- Summary ---
        label = "AVERAGE COMPONENTS" if component == 'average' else component.upper()
        label += " - AVERAGE INTENSITIES" if intensity == 'average' else f" - {intensity.upper()}"
        
        summary_info = html.Div([
            html.H5("Aggregated Analysis Summary", style={"color": "#2c3e50", "marginBottom": "10px"}),
            html.P(f"**Configuration:** {label}"),
            html.P(f"**Total Experiments Analyzed:** {len(unique_experiments)}"),
            html.P(f"**Energy Source:** {energy_source.title()}"),
            html.P(f"**Node Filter:** {selected_node or 'All Nodes'}")
        ])
        
        return [fig_energy_node, fig_energy_comp, fig_transactions, fig_response, fig_process, fig_timeline, summary_info]
        
    except Exception as e:
        error_msg = f"Error in aggregated analysis: {str(e)}"
        empty = create_empty_figure(error_msg)
        return [empty]*6 + [html.Div([html.H5("Error", style={"color": "#e74c3c"}), html.P(error_msg)])]


# --- LAYOUT ---

app.layout = html.Div([
    html.H1("Consolidated Average Analysis View", style={"textAlign": "center", "marginBottom": 30, "color": "#2c3e50"}),
    
    # Global Component Selector
    html.Div([
        html.Label("Select Component to Analyze:", style={"fontWeight": "bold", "marginRight": "10px"}),
        dcc.Dropdown(
            id="global-component-dropdown",
            options=[{'label': c.upper(), 'value': c} for c in data_loader.get_available_components()] + [{'label': 'AVERAGE COMPONENTS', 'value': 'average'}],
            placeholder="Select Component",
            style={"width": "300px", "display": "inline-block"}
        ),
    ], style={"textAlign": "center", "marginBottom": "30px"}),

    # Tabs
    dcc.Tabs([
        # TAB 1: By Intensity
        dcc.Tab(label='Analysis by Intensity', children=[
            html.Div([
                html.Div([
                    html.Label("Select Intensity:", style={"fontWeight": "bold", "marginRight": "10px"}),
                    dcc.Dropdown(
                        id="tab1-intensity-dropdown",
                        placeholder="Select Intensity",
                        style={"width": "200px", "display": "inline-block"}
                    ),
                ], style={"padding": "20px", "backgroundColor": "#ecf0f1", "borderRadius": "5px", "marginBottom": "20px"}),
                
                # Grid for Tab 1
                create_dashboard_grid("tab1")
            ], style={"padding": "20px"})
        ]),

        # TAB 2: Global Summary
        dcc.Tab(label='Global Summary (All Intensities)', children=[
            html.Div([
                html.Div([
                    html.P("Click the button below to aggregate data from ALL available intensities (High, Med, Low, etc.) for the selected component.", style={"color": "#7f8c8d"}),
                    html.Button('Calculate Global Averages', id='btn-calculate-global', n_clicks=0, 
                               style={"backgroundColor": "#2980b9", "color": "white", "padding": "10px 20px", "border": "none", "borderRadius": "5px", "cursor": "pointer", "fontSize": "16px"})
                ], style={"textAlign": "center", "padding": "20px", "backgroundColor": "#ecf0f1", "borderRadius": "5px", "marginBottom": "20px"}),

                dcc.Loading(
                    id="loading-global",
                    type="default",
                    children=create_dashboard_grid("global")
                )
            ], style={"padding": "20px"})
        ]),

        # TAB 3: Granular Analysis (New)
        dcc.Tab(label='Granular Layer Analysis', children=[
            html.Div([
                # Filters Section
                html.Div([
                    html.H4("Granular Filters", style={"color": "#2c3e50", "marginBottom": "15px"}),
                    html.Div([
                        # Row 1: Component, Intensity, Experiment
                        html.Div([
                            html.Div([
                                html.Label("Intensity:", style={"fontWeight": "bold", "marginRight": "10px"}),
                                dcc.Dropdown(id="granular-intensity-dropdown", placeholder="Select Intensity", style={"width": "150px"})
                            ], style={"display": "inline-block", "marginRight": "20px"}),
                            html.Div([
                                html.Label("Experiment:", style={"fontWeight": "bold", "marginRight": "10px"}),
                                dcc.Dropdown(id="granular-experiment-dropdown", placeholder="Select Experiment", style={"width": "300px"})
                            ], style={"display": "inline-block", "marginRight": "20px"}),
                        ], style={"marginBottom": "15px"}),
                        
                        # Row 2: Node, Filter Type, Metric Type
                        html.Div([
                            html.Div([
                                html.Label("Node:", style={"fontWeight": "bold", "marginRight": "10px"}),
                                dcc.Dropdown(id="granular-node-dropdown", placeholder="All Nodes", style={"width": "150px"})
                            ], style={"display": "inline-block", "marginRight": "20px"}),
                            html.Div([
                                html.Label("Filter by:", style={"fontWeight": "bold", "marginRight": "10px"}),
                                dcc.Dropdown(
                                    id="granular-filter-type",
                                    options=[
                                        {"label": "All Data", "value": "all"},
                                        {"label": "Successful Requests", "value": "success"},
                                        {"label": "Failed Requests", "value": "failed"},
                                        {"label": "Dropped Requests", "value": "dropped"},
                                        {"label": "High Response Time", "value": "high_response"},
                                        {"label": "Energy Intensive", "value": "high_energy"}
                                    ],
                                    value="all",
                                    style={"width": "180px"}
                                )
                            ], style={"display": "inline-block", "marginRight": "20px"}),
                            html.Div([
                                html.Label("Energy Source:", style={"fontWeight": "bold", "marginRight": "10px"}),
                                dcc.RadioItems(
                                    id="granular-energy-source",
                                    options=[
                                        {"label": "Ecofloc", "value": "ecofloc"},
                                        {"label": "Scaphandre", "value": "scaphandre"}
                                    ],
                                    value="ecofloc",
                                    inline=True
                                )
                            ], style={"display": "inline-block"}),
                        ], style={"marginBottom": "20px"}),
                    ])
                ], style={"backgroundColor": "#ecf0f1", "padding": "20px", "borderRadius": "5px", "marginBottom": "20px"}),
                
                # Analysis Button
                html.Div([
                    html.Button('Generate Granular Analysis', id='btn-granular-analysis', n_clicks=0,
                               style={"backgroundColor": "#e74c3c", "color": "white", "padding": "12px 25px", "border": "none", "borderRadius": "5px", "cursor": "pointer", "fontSize": "16px", "fontWeight": "bold"})
                ], style={"textAlign": "center", "marginBottom": "30px"}),
                
                # Results Section
                dcc.Loading(
                    id="loading-granular",
                    type="default",
                    children=[
                        # Energy Analysis Row
                        html.Div([
                            html.H4("Energy Analysis by Layer", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            html.Div([
                                html.Div([dcc.Graph(id="granular-energy-by-node")], style={"width": "48%", "display": "inline-block", "marginRight": "2%"}),
                                html.Div([dcc.Graph(id="granular-energy-by-component")], style={"width": "48%", "display": "inline-block"}),
                            ], style={"marginBottom": "30px"}),
                        ]),
                        
                        # Performance Analysis Row  
                        html.Div([
                            html.H4("Performance Metrics Analysis", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            html.Div([
                                html.Div([dcc.Graph(id="granular-transaction-breakdown")], style={"width": "48%", "display": "inline-block", "marginRight": "2%"}),
                                html.Div([dcc.Graph(id="granular-response-time-dist")], style={"width": "48%", "display": "inline-block"}),
                            ], style={"marginBottom": "30px"}),
                        ]),
                        
                        # Process Level Analysis Row
                        html.Div([
                            html.H4("Process-Level Analysis", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            html.Div([
                                html.Div([dcc.Graph(id="granular-process-energy")], style={"width": "48%", "display": "inline-block", "marginRight": "2%"}),
                                html.Div([dcc.Graph(id="granular-energy-timeline")], style={"width": "48%", "display": "inline-block"}),
                            ], style={"marginBottom": "30px"}),
                        ]),
                        
                        # Summary Info
                        html.Div(id="granular-summary-info", style={"backgroundColor": "#f8f9fa", "padding": "15px", "borderRadius": "5px", "marginTop": "20px"})
                    ]
                )
            ], style={"padding": "20px"})
        ]),

        # TAB 4: Process/Pod Energy Comparison
        dcc.Tab(label='Process Energy Comparison', children=[
            html.Div([
                # Filters Section
                html.Div([
                    html.H4("Process Energy Comparison Filters", style={"color": "#2c3e50", "marginBottom": "15px"}),
                    html.Div([
                        # Row 1: Component, Intensity selection
                        html.Div([
                            html.Div([
                                html.Label("Component:", style={"fontWeight": "bold", "marginRight": "10px"}),
                                dcc.Dropdown(
                                    id="process-component-dropdown",
                                    options=[
                                        {"label": "CPU", "value": "cpu"},
                                        {"label": "RAM", "value": "ram"},
                                        {"label": "NIC", "value": "nic"},
                                        {"label": "SD", "value": "sd"},
                                        {"label": "ALL COMPONENTS (Aggregated)", "value": "all"}
                                    ],
                                    value="cpu",
                                    style={"width": "200px"}
                                )
                            ], style={"display": "inline-block", "marginRight": "20px"}),
                            html.Div([
                                html.Label("Intensity:", style={"fontWeight": "bold", "marginRight": "10px"}),
                                dcc.Dropdown(id="process-intensity-dropdown", placeholder="Select Intensity", style={"width": "150px"})
                            ], style={"display": "inline-block", "marginRight": "20px"}),
                            html.Div([
                                html.Label("Experiment:", style={"fontWeight": "bold", "marginRight": "10px"}),
                                dcc.Dropdown(id="process-experiment-dropdown", placeholder="Select Experiment", style={"width": "300px"})
                            ], style={"display": "inline-block"}),
                        ], style={"marginBottom": "15px"}),
                        
                        # Row 2: Process/Pod filter and comparison mode
                        html.Div([
                            html.Div([
                                html.Label("Process/Pod Filter:", style={"fontWeight": "bold", "marginRight": "10px"}),
                                dcc.Dropdown(
                                    id="process-name-dropdown",
                                    placeholder="All Processes",
                                    multi=True,
                                    style={"width": "400px"}
                                )
                            ], style={"display": "inline-block", "marginRight": "20px"}),
                            html.Div([
                                html.Label("Comparison Mode:", style={"fontWeight": "bold", "marginRight": "10px"}),
                                dcc.RadioItems(
                                    id="process-comparison-mode",
                                    options=[
                                        {"label": "By Node (same process across nodes)", "value": "by_node"},
                                        {"label": "By Component (energy breakdown per process)", "value": "by_component"},
                                        {"label": "General Overview", "value": "overview"}
                                    ],
                                    value="overview",
                                    inline=True
                                )
                            ], style={"display": "inline-block"}),
                        ], style={"marginBottom": "20px"}),
                    ])
                ], style={"backgroundColor": "#ecf0f1", "padding": "20px", "borderRadius": "5px", "marginBottom": "20px"}),
                
                # Analysis Button
                html.Div([
                    html.Button('Generate Process Analysis', id='btn-process-analysis', n_clicks=0,
                               style={"backgroundColor": "#9b59b6", "color": "white", "padding": "12px 25px", "border": "none", "borderRadius": "5px", "cursor": "pointer", "fontSize": "16px", "fontWeight": "bold"})
                ], style={"textAlign": "center", "marginBottom": "30px"}),
                
                # Results Section
                dcc.Loading(
                    id="loading-process",
                    type="default",
                    children=[
                        # Row 1: Main comparison chart
                        html.Div([
                            html.H4("Process Energy Comparison", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            dcc.Graph(id="process-main-comparison-chart"),
                        ], style={"marginBottom": "30px"}),
                        
                        # Row 2: Per-node breakdown
                        html.Div([
                            html.H4("Energy by Node", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            html.Div([
                                html.Div([dcc.Graph(id="process-node-chart-1")], style={"width": "48%", "display": "inline-block", "marginRight": "2%"}),
                                html.Div([dcc.Graph(id="process-node-chart-2")], style={"width": "48%", "display": "inline-block"}),
                            ], style={"marginBottom": "20px"}),
                            html.Div([
                                html.Div([dcc.Graph(id="process-node-chart-3")], style={"width": "48%", "display": "inline-block", "marginRight": "2%"}),
                                html.Div([dcc.Graph(id="process-node-chart-4")], style={"width": "48%", "display": "inline-block"}),
                            ]),
                        ], style={"marginBottom": "30px"}),
                        
                        # Row 3: Component breakdown per process
                        html.Div([
                            html.H4("Component Energy Breakdown per Process", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            dcc.Graph(id="process-component-breakdown-chart"),
                        ], style={"marginBottom": "30px"}),
                        
                        # Row 4: Heatmap comparison
                        html.Div([
                            html.H4("Process-Node Energy Heatmap", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            dcc.Graph(id="process-heatmap-chart"),
                        ], style={"marginBottom": "30px"}),
                        
                        # Summary Table
                        html.Div(id="process-summary-table", style={"backgroundColor": "#f8f9fa", "padding": "15px", "borderRadius": "5px", "marginTop": "20px"})
                    ]
                )
            ], style={"padding": "20px"})
        ]),

        # TAB 5: Scheduler Analysis
        dcc.Tab(label='Scheduler Preferences Analysis', children=[
            html.Div([
                # Header
                html.Div([
                    html.H4("Kubernetes Scheduler Behavior Analysis", style={"color": "#2c3e50", "marginBottom": "10px"}),
                    html.P("Analyze how the Kubernetes scheduler distributes pods across nodes over 1000 iterations.", 
                           style={"color": "#7f8c8d", "marginBottom": "15px"}),
                    html.Button('Load Scheduler Data', id='btn-scheduler-analysis', n_clicks=0,
                               style={"backgroundColor": "#16a085", "color": "white", "padding": "12px 25px", "border": "none", "borderRadius": "5px", "cursor": "pointer", "fontSize": "16px", "fontWeight": "bold"})
                ], style={"backgroundColor": "#ecf0f1", "padding": "20px", "borderRadius": "5px", "marginBottom": "20px", "textAlign": "center"}),
                
                # Results Section
                dcc.Loading(
                    id="loading-scheduler",
                    type="default",
                    children=[
                        # Row 1: Overall distribution
                        html.Div([
                            html.H4("1. Overall Node Preference", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            html.Div([
                                html.Div([dcc.Graph(id="scheduler-node-distribution")], style={"width": "48%", "display": "inline-block", "marginRight": "2%"}),
                                html.Div([dcc.Graph(id="scheduler-node-pie")], style={"width": "48%", "display": "inline-block"}),
                            ]),
                        ], style={"marginBottom": "30px"}),
                        
                        # Row 2: Service-Node Heatmap
                        html.Div([
                            html.H4("2. Service-Node Assignment Heatmap", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            html.P("Which nodes does the scheduler prefer for each service type?", style={"color": "#7f8c8d"}),
                            dcc.Graph(id="scheduler-service-node-heatmap"),
                        ], style={"marginBottom": "30px"}),
                        
                        # Row 3: Per-service distribution
                        html.Div([
                            html.H4("3. Node Preference by Service Type", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            html.P("How each service type is distributed across nodes (normalized percentage)", style={"color": "#7f8c8d"}),
                            dcc.Graph(id="scheduler-service-distribution"),
                        ], style={"marginBottom": "30px"}),
                        
                        # Row 4: Temporal analysis
                        html.Div([
                            html.H4("4. Node Load Over Time (Pods per Node)", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            html.P("How many pods are assigned to each node across iterations", style={"color": "#7f8c8d"}),
                            dcc.Graph(id="scheduler-temporal-distribution"),
                        ], style={"marginBottom": "30px"}),
                        
                        # Row 5: Node balance per iteration
                        html.Div([
                            html.H4("5. Node Balance Analysis", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            html.Div([
                                html.Div([dcc.Graph(id="scheduler-balance-boxplot")], style={"width": "48%", "display": "inline-block", "marginRight": "2%"}),
                                html.Div([dcc.Graph(id="scheduler-balance-violin")], style={"width": "48%", "display": "inline-block"}),
                            ]),
                        ], style={"marginBottom": "30px"}),
                        
                        # Row 6: Co-location patterns
                        html.Div([
                            html.H4("6. Service Co-location Patterns", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            html.P("Which services tend to be placed on the same node together?", style={"color": "#7f8c8d"}),
                            dcc.Graph(id="scheduler-colocation-heatmap"),
                        ], style={"marginBottom": "30px"}),
                        
                        # Row 7: Most common configurations
                        html.Div([
                            html.H4("7. Most Common Pod-Node Configurations", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            html.P("Top 10 most frequently observed complete configurations", style={"color": "#7f8c8d"}),
                            dcc.Graph(id="scheduler-top-configurations"),
                        ], style={"marginBottom": "30px"}),
                        
                        # Summary Statistics
                        html.Div(id="scheduler-summary-stats", style={"backgroundColor": "#f8f9fa", "padding": "15px", "borderRadius": "5px", "marginTop": "20px"})
                    ]
                )
            ], style={"padding": "20px"})
        ]),
        
        # TAB 6: Energy Score Manager for Kubernetes Scheduler
        dcc.Tab(label='⚡ Energy Score Manager', children=[
            html.Div([
                # Header
                html.Div([
                    html.H4("Kubernetes Node Energy Score Manager", style={"color": "#2c3e50", "marginBottom": "10px"}),
                    html.P([
                        "Calcula y aplica puntajes de eficiencia energética a los nodos de Kubernetes. ",
                        html.Br(),
                        "El scheduler lee el label ", 
                        html.Code("energy-score"), 
                        " para tomar decisiones de scheduling basadas en eficiencia energética."
                    ], style={"color": "#7f8c8d", "marginBottom": "15px"}),
                    
                    html.Div([
                        html.Div([
                            html.Label("Fuente de Energía:", style={"fontWeight": "bold", "marginRight": "10px"}),
                            dcc.RadioItems(
                                id="energy-score-source",
                                options=[
                                    {"label": "Ecofloc (CPU, RAM, NIC, SD)", "value": "ecofloc"},
                                    {"label": "Scaphandre (Global/CPU)", "value": "scaphandre"}
                                ],
                                value="ecofloc",
                                inline=True
                            )
                        ], style={"display": "inline-block", "marginRight": "30px"}),
                        
                        html.Button('🔄 Calcular Scores', id='btn-calculate-energy-scores', n_clicks=0,
                                   style={"backgroundColor": "#27ae60", "color": "white", "padding": "10px 20px", 
                                          "border": "none", "borderRadius": "5px", "cursor": "pointer", 
                                          "fontSize": "14px", "fontWeight": "bold", "marginRight": "10px"}),
                        
                        html.Button('🚀 Aplicar a Kubernetes', id='btn-apply-energy-scores', n_clicks=0,
                                   style={"backgroundColor": "#e74c3c", "color": "white", "padding": "10px 20px", 
                                          "border": "none", "borderRadius": "5px", "cursor": "pointer", 
                                          "fontSize": "14px", "fontWeight": "bold"}),
                    ], style={"marginTop": "15px"})
                    
                ], style={"backgroundColor": "#ecf0f1", "padding": "20px", "borderRadius": "5px", "marginBottom": "20px", "textAlign": "center"}),
                
                # Status Message
                html.Div(id="energy-score-status", style={"padding": "10px", "marginBottom": "20px"}),
                
                # Results Section
                dcc.Loading(
                    id="loading-energy-scores",
                    type="default",
                    children=[
                        # Row 1: Current Kubernetes nodes and Energy Scores comparison
                        html.Div([
                            html.H4("1. Estado Actual de Nodos Kubernetes", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            html.Div([
                                html.Div([dcc.Graph(id="energy-k8s-nodes-table")], style={"width": "48%", "display": "inline-block", "marginRight": "2%"}),
                                html.Div([dcc.Graph(id="energy-scores-bar-chart")], style={"width": "48%", "display": "inline-block"}),
                            ]),
                        ], style={"marginBottom": "30px"}),
                        
                        # Row 2: Component breakdown
                        html.Div([
                            html.H4("2. Desglose de Energía por Componente y Nodo", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            html.Div([
                                html.Div([dcc.Graph(id="energy-component-breakdown")], style={"width": "48%", "display": "inline-block", "marginRight": "2%"}),
                                html.Div([dcc.Graph(id="energy-efficiency-radar")], style={"width": "48%", "display": "inline-block"}),
                            ]),
                        ], style={"marginBottom": "30px"}),
                        
                        # Row 3: Score calculation details
                        html.Div([
                            html.H4("3. Cálculo de Puntajes", style={"color": "#2c3e50", "marginBottom": "20px"}),
                            html.Div([
                                html.Div([dcc.Graph(id="energy-score-weights")], style={"width": "48%", "display": "inline-block", "marginRight": "2%"}),
                                html.Div([dcc.Graph(id="energy-score-ranking")], style={"width": "48%", "display": "inline-block"}),
                            ]),
                        ], style={"marginBottom": "30px"}),
                        
                        # Summary and Commands
                        html.Div(id="energy-score-summary", style={"backgroundColor": "#f8f9fa", "padding": "15px", "borderRadius": "5px", "marginTop": "20px"})
                    ]
                )
            ], style={"padding": "20px"})
        ]),
    ])

], style={"maxWidth": "1500px", "margin": "0 auto", "fontFamily": "Segoe UI, Arial, sans-serif", "padding": "20px"})


# --- CALLBACKS ---

# Populate Intensity Dropdown for Tab 1
@app.callback(
    Output("tab1-intensity-dropdown", "options"),
    Input("global-component-dropdown", "value")
)
def update_intensities(component):
    if not component: return []
    if component == 'average':
        # For average components, show all possible intensities
        all_intensities = set()
        for comp in ['cpu', 'ram', 'nic', 'sd']:
            all_intensities.update(data_loader.get_available_intensities(comp))
        return [{"label": i.upper(), "value": i} for i in sorted(all_intensities)] + [{"label": "AVERAGE INTENSITIES", "value": "average"}]
    intensities = data_loader.get_available_intensities(component)
    return [{"label": i.upper(), "value": i} for i in intensities] + [{"label": "AVERAGE INTENSITIES", "value": "average"}]


# Update Graphs for Tab 1 (By Intensity)
@app.callback(
    Output("tab1-absolute-energy-chart", "figure"),
    Output("tab1-normalized-energy-chart", "figure"),
    Output("tab1-scaphandre-chart", "figure"), # Nuevo Output
    Output("tab1-load-chart", "figure"),
    Output("tab1-success-chart", "figure"),
    Output("tab1-failed-chart", "figure"),
    Output("tab1-dropped-chart", "figure"),
    Output("tab1-response-chart", "figure"),
    Output("tab1-dispatch-chart", "figure"),
    Output("tab1-badge", "children"),
    Input("global-component-dropdown", "value"),
    Input("tab1-intensity-dropdown", "value")
)
def update_tab1_graphs(component, intensity):
    if not component or not intensity:
        return [go.Figure().update_layout(title="Select Component and Intensity")] * 9 + [""]
    
    # Handle average component case
    if component == 'average':
        all_experiments = []
        for comp in ['cpu', 'ram', 'nic', 'sd']:
            if intensity == 'average':
                # Average all intensities for all components
                for intens in data_loader.get_available_intensities(comp):
                    all_experiments.extend(data_loader.get_available_experiments(comp, intens))
            else:
                all_experiments.extend(data_loader.get_available_experiments(comp, intensity))
        unique_experiments = {exp['value']: exp for exp in all_experiments}.values()
        label = "AVERAGE COMPONENTS" + (" - AVERAGE INTENSITIES" if intensity == 'average' else f" - {intensity.upper()}")
        return generate_figures_from_experiments(list(unique_experiments), label)
    
    # Handle average intensity for single component
    if intensity == 'average':
        all_experiments = []
        for intens in data_loader.get_available_intensities(component):
            all_experiments.extend(data_loader.get_available_experiments(component, intens))
        unique_experiments = {exp['value']: exp for exp in all_experiments}.values()
        return generate_figures_from_experiments(list(unique_experiments), f"{component.upper()} - AVERAGE INTENSITIES")
    
    experiments = data_loader.get_available_experiments(component, intensity)
    return generate_figures_from_experiments(experiments, intensity.upper())


# Update Graphs for Tab 2 (Global)
@app.callback(
    Output("global-absolute-energy-chart", "figure"),
    Output("global-normalized-energy-chart", "figure"),
    Output("global-scaphandre-chart", "figure"), # Nuevo Output
    Output("global-load-chart", "figure"),
    Output("global-success-chart", "figure"),
    Output("global-failed-chart", "figure"),
    Output("global-dropped-chart", "figure"),
    Output("global-response-chart", "figure"),
    Output("global-dispatch-chart", "figure"),
    Output("global-badge", "children"),
    Input("btn-calculate-global", "n_clicks"),
    State("global-component-dropdown", "value")
)
def update_global_graphs(n_clicks, component):
    if n_clicks == 0 or not component:
        return [go.Figure().update_layout(title="Click Calculate to load data")] * 9 + [""]
    
    # Handle average components case (promedio de los 4 componentes)
    if component == 'average':
        all_experiments = []
        for comp in ['cpu', 'ram', 'nic', 'sd']:
            intensities = data_loader.get_available_intensities(comp)
            for intensity in intensities:
                exps = data_loader.get_available_experiments(comp, intensity)
                all_experiments.extend(exps)
        
        # Eliminar duplicados si los hubiera (basado en path)
        unique_experiments = {exp['value']: exp for exp in all_experiments}.values()
        return generate_figures_from_experiments(list(unique_experiments), "AVERAGE COMPONENTS (ALL INTENSITIES)")
    
    # 1. Obtener todas las intensidades disponibles
    intensities = data_loader.get_available_intensities(component)
    
    # 2. Recolectar experimentos de TODAS las intensidades
    all_experiments = []
    for intensity in intensities:
        exps = data_loader.get_available_experiments(component, intensity)
        all_experiments.extend(exps)
        
    # Eliminar duplicados si los hubiera (basado en path)
    unique_experiments = {exp['value']: exp for exp in all_experiments}.values()
    
    return generate_figures_from_experiments(list(unique_experiments), "ALL INTENSITIES")


# --- NEW GRANULAR CALLBACKS ---

# Populate granular intensity dropdown
@app.callback(
    Output("granular-intensity-dropdown", "options"),
    Input("global-component-dropdown", "value")
)
def populate_granular_intensities(component):
    if not component: return []
    if component == 'average':
        # For average components, show all possible intensities from all components
        all_intensities = set()
        for comp in ['cpu', 'ram', 'nic', 'sd']:
            all_intensities.update(data_loader.get_available_intensities(comp))
        return [{"label": i.upper(), "value": i} for i in sorted(all_intensities)] + [{"label": "AVERAGE INTENSITIES", "value": "average"}]
    intensities = data_loader.get_available_intensities(component)
    return [{"label": i.upper(), "value": i} for i in intensities] + [{"label": "AVERAGE INTENSITIES", "value": "average"}]

# Populate granular experiment dropdown
@app.callback(
    Output("granular-experiment-dropdown", "options"),
    Output("granular-experiment-dropdown", "value"),
    Input("global-component-dropdown", "value"),
    Input("granular-intensity-dropdown", "value")
)
def populate_granular_experiments(component, intensity):
    if not component or not intensity: return [], None
    
    all_experiments = []
    
    # Handle average component + average intensity case (auto-select all)
    if component == 'average' and intensity == 'average':
        for comp in ['cpu', 'ram', 'nic', 'sd']:
            for intens in data_loader.get_available_intensities(comp):
                all_experiments.extend(data_loader.get_available_experiments(comp, intens))
        # Remove duplicates
        unique_experiments = {exp['value']: exp for exp in all_experiments}.values()
        # Return ALL EXPERIMENTS option auto-selected
        return [{"label": f"ALL EXPERIMENTS ({len(list(unique_experiments))} total)", "value": "all_experiments"}], "all_experiments"
    
    # Handle average component case
    if component == 'average':
        for comp in ['cpu', 'ram', 'nic', 'sd']:
            all_experiments.extend(data_loader.get_available_experiments(comp, intensity))
    # Handle average intensity for single component
    elif intensity == 'average':
        for intens in data_loader.get_available_intensities(component):
            all_experiments.extend(data_loader.get_available_experiments(component, intens))
        # For single component with average intensity, also offer ALL EXPERIMENTS option
        unique_experiments = {exp['value']: exp for exp in all_experiments}.values()
        options = [{"label": f"ALL EXPERIMENTS ({len(list(unique_experiments))} total)", "value": "all_experiments"}]
        options.extend([{"label": exp["label"], "value": exp["value"]} for exp in unique_experiments])
        return options, "all_experiments"
    # Normal case
    else:
        all_experiments = data_loader.get_available_experiments(component, intensity)
    
    # Remove duplicates based on path
    unique_experiments = {exp['value']: exp for exp in all_experiments}.values()
    return [{"label": exp["label"], "value": exp["value"]} for exp in unique_experiments], None

# Populate granular node dropdown  
@app.callback(
    Output("granular-node-dropdown", "options"),
    Input("granular-experiment-dropdown", "value"),
    State("global-component-dropdown", "value")
)
def populate_granular_nodes(experiment_path, component):
    if not experiment_path or not component: 
        return [{"label": "All Nodes", "value": "all"}]
    
    try:
        # Try to get nodes from informe_pids.csv
        pids_df = data_loader.load_informe_pids(experiment_path)
        if not pids_df.empty and 'node_name' in pids_df.columns:
            unique_nodes = sorted(pids_df["node_name"].unique())
            options = [{"label": "All Nodes", "value": "all"}]
            options.extend([{"label": node, "value": node} for node in unique_nodes])
            return options
        
        # Fallback: try to get nodes from energy data
        ecofloc_df = data_loader.load_ecofloc_component_data(experiment_path, 'cpu')
        if not ecofloc_df.empty and 'node_name' in ecofloc_df.columns:
            unique_nodes = sorted(ecofloc_df["node_name"].unique())
            options = [{"label": "All Nodes", "value": "all"}]
            options.extend([{"label": node, "value": node} for node in unique_nodes])
            return options
            
    except Exception as e:
        print(f"Error loading nodes: {e}")
    
    return [{"label": "All Nodes", "value": "all"}]

# Main granular analysis callback
@app.callback(
    Output("granular-energy-by-node", "figure"),
    Output("granular-energy-by-component", "figure"),
    Output("granular-transaction-breakdown", "figure"),
    Output("granular-response-time-dist", "figure"),
    Output("granular-process-energy", "figure"),
    Output("granular-energy-timeline", "figure"),
    Output("granular-summary-info", "children"),
    Input("btn-granular-analysis", "n_clicks"),
    State("global-component-dropdown", "value"),
    State("granular-intensity-dropdown", "value"),
    State("granular-experiment-dropdown", "value"),
    State("granular-node-dropdown", "value"),
    State("granular-filter-type", "value"),
    State("granular-energy-source", "value")
)
def update_granular_analysis(n_clicks, component, intensity, experiment_path, selected_node, filter_type, energy_source):
    if n_clicks == 0 or not component or not intensity:
        empty = create_empty_figure("Please select filters and click Generate Analysis")
        return [empty]*6 + ["Please configure filters above and click the Generate button."]
    
    # Handle 'all_experiments' case - load data from all experiments
    if experiment_path == 'all_experiments' or (component == 'average' and intensity == 'average'):
        return generate_granular_all_experiments(component, intensity, selected_node, filter_type, energy_source)
    
    if not experiment_path:
        empty = create_empty_figure("Please select an experiment")
        return [empty]*6 + ["Please select an experiment."]
    
    try:
        # Determine actual intensity for loading (if 'average', try common intensities)
        actual_intensity = intensity if intensity != 'average' else 'low'
        
        # Load data
        limbo_df = data_loader.load_limbo_data(experiment_path, actual_intensity)
        
        # If average was selected and data is empty, try other intensities
        if intensity == 'average' and limbo_df.empty:
            for int_option in ['med', 'high', 'specific-scenarios']:
                limbo_df = data_loader.load_limbo_data(experiment_path, int_option)
                if not limbo_df.empty:
                    break
        
        # Load energy data based on source
        if energy_source == "ecofloc":
            cpu_df = data_loader.load_ecofloc_component_data(experiment_path, 'cpu')
            ram_df = data_loader.load_ecofloc_component_data(experiment_path, 'ram') 
            sd_df = data_loader.load_ecofloc_component_data(experiment_path, 'sd')
            nic_df = data_loader.load_ecofloc_component_data(experiment_path, 'nic')
        else:
            scap_df = data_loader.load_scaphandre_data(experiment_path)
        
        # Load process data
        try:
            pids_df = data_loader.load_informe_pids(experiment_path)
        except:
            pids_df = pd.DataFrame()
        
        # --- 1. Energy by Node ---
        if energy_source == "ecofloc":
            node_energy_data = []
            for comp_name, df in [("CPU", cpu_df), ("RAM", ram_df), ("SD", sd_df), ("NIC", nic_df)]:
                if not df.empty:
                    node_totals = df.groupby('node_name')['energy_value'].sum().reset_index()
                    node_totals['component'] = comp_name
                    node_energy_data.append(node_totals)
            
            if node_energy_data:
                all_energy_df = pd.concat(node_energy_data)
                
                # Filter by node if specified
                if selected_node and selected_node != "all":
                    all_energy_df = all_energy_df[all_energy_df['node_name'] == selected_node]
                
                fig_energy_node = px.bar(
                    all_energy_df, x="node_name", y="energy_value", color="component", 
                    barmode="group", title=f"Energy Consumption by Node ({energy_source.title()})",
                    labels={"energy_value": "Energy (Joules)", "node_name": "Node"}
                )
            else:
                fig_energy_node = create_empty_figure("No energy data available")
        else:
            # Scaphandre
            if not scap_df.empty:
                node_totals = scap_df.groupby('node_name')['energy_value'].sum().reset_index()
                if selected_node and selected_node != "all":
                    node_totals = node_totals[node_totals['node_name'] == selected_node]
                    
                fig_energy_node = px.bar(
                    node_totals, x="node_name", y="energy_value",
                    title=f"Energy Consumption by Node ({energy_source.title()})",
                    labels={"energy_value": "Energy (Joules)", "node_name": "Node"},
                    color_discrete_sequence=['#e67e22']
                )
            else:
                fig_energy_node = create_empty_figure("No Scaphandre data available")
        
        # --- 2. Energy by Component ---
        if energy_source == "ecofloc" and node_energy_data:
            component_totals = all_energy_df.groupby('component')['energy_value'].sum().reset_index()
            fig_energy_comp = px.pie(
                component_totals, values="energy_value", names="component",
                title="Energy Distribution by Component", hole=0.4
            )
        else:
            fig_energy_comp = create_empty_figure("Component breakdown only available for Ecofloc")
        
        # --- 3. Transaction Breakdown ---
        if not limbo_df.empty:
            # Apply filtering based on filter_type
            if filter_type == "success":
                filtered_df = limbo_df[limbo_df.get('successful_transactions', 0) > 0]
                title_suffix = " (Successful Requests Only)"
            elif filter_type == "failed":
                filtered_df = limbo_df[limbo_df.get('failed_transactions', 0) > 0]
                title_suffix = " (Failed Requests Only)"
            elif filter_type == "dropped":
                filtered_df = limbo_df[limbo_df.get('dropped_transactions', 0) > 0]
                title_suffix = " (Dropped Requests Only)"
            elif filter_type == "high_response":
                # Filter for above-average response times
                avg_resp = limbo_df['avg_response_time'].mean()
                filtered_df = limbo_df[limbo_df['avg_response_time'] > avg_resp]
                title_suffix = " (High Response Time)"
            else:
                filtered_df = limbo_df
                title_suffix = ""
            
            if not filtered_df.empty:
                # Calculate totals
                total_success = filtered_df.get('successful_transactions', pd.Series([0])).sum()
                total_failed = filtered_df.get('failed_transactions', pd.Series([0])).sum()
                total_dropped = filtered_df.get('dropped_transactions', pd.Series([0])).sum()
                
                fig_transactions = px.pie(
                    values=[total_success, total_failed, total_dropped],
                    names=["Successful", "Failed", "Dropped"],
                    title=f"Transaction Breakdown{title_suffix}",
                    color_discrete_map={
                        "Successful": "green",
                        "Failed": "red", 
                        "Dropped": "orange"
                    }
                )
            else:
                fig_transactions = create_empty_figure("No data matches the selected filter")
        else:
            fig_transactions = create_empty_figure("No benchmark data available")
        
        # --- 4. Response Time Distribution ---
        if not limbo_df.empty and 'avg_response_time' in limbo_df.columns:
            fig_response = px.histogram(
                limbo_df, x="avg_response_time", nbins=20,
                title="Response Time Distribution",
                labels={"avg_response_time": "Response Time (s)", "count": "Frequency"}
            )
        else:
            fig_response = create_empty_figure("No response time data available")
        
        # --- 5. Process Energy (if available) ---
        if not pids_df.empty and energy_source == "ecofloc" and not cpu_df.empty:
            try:
                # Merge with process names
                process_energy = cpu_df.groupby(['node_name', 'pid'])['energy_value'].sum().reset_index()
                process_merged = process_energy.merge(pids_df, on=['node_name', 'pid'], how='inner')
                
                if selected_node and selected_node != "all":
                    process_merged = process_merged[process_merged['node_name'] == selected_node]
                
                if not process_merged.empty:
                    # Get top 10 energy-consuming processes
                    top_processes = process_merged.nlargest(10, 'energy_value')
                    
                    fig_process = px.bar(
                        top_processes, x="name_pid", y="energy_value",
                        title="Top 10 Energy-Consuming Processes",
                        labels={"name_pid": "Process", "energy_value": "Energy (Joules)"}
                    )
                    fig_process.update_xaxis(tickangle=45)
                else:
                    fig_process = create_empty_figure("No process data available")
            except Exception as e:
                fig_process = create_empty_figure(f"Error loading process data: {str(e)}")
        else:
            fig_process = create_empty_figure("Process analysis requires Ecofloc data and PID information")
        
        # --- 6. Energy Timeline ---
        if energy_source == "ecofloc" and not cpu_df.empty:
            timeline_df = cpu_df.copy()
            if selected_node and selected_node != "all":
                timeline_df = timeline_df[timeline_df['node_name'] == selected_node]
            
            if not timeline_df.empty and 'elapsed_seconds' in timeline_df.columns:
                fig_timeline = go.Figure()
                for node in timeline_df['node_name'].unique():
                    node_data = timeline_df[timeline_df['node_name'] == node].sort_values('elapsed_seconds')
                    fig_timeline.add_trace(go.Scatter(
                        x=node_data['elapsed_seconds'],
                        y=node_data['energy_value'],
                        mode='lines+markers',
                        name=f'Node {node}',
                        line=dict(width=2),
                        marker=dict(size=4)
                    ))
                
                fig_timeline.update_layout(
                    title="Energy Consumption Timeline",
                    xaxis_title="Time (seconds)",
                    yaxis_title="Energy (Joules)",
                    template="plotly_white"
                )
            else:
                fig_timeline = create_empty_figure("No timeline data available")
        else:
            fig_timeline = create_empty_figure("Timeline requires Ecofloc data with timestamps")
        
        # --- Summary Info ---
        summary_parts = []
        summary_parts.append(f"**Analysis Configuration:** Component: {component.upper()}, Intensity: {intensity.upper()}, Energy Source: {energy_source.title()}")
        
        if not limbo_df.empty:
            total_requests = limbo_df.get('successful_transactions', pd.Series([0])).sum() + limbo_df.get('failed_transactions', pd.Series([0])).sum() + limbo_df.get('dropped_transactions', pd.Series([0])).sum()
            avg_response = limbo_df.get('avg_response_time', pd.Series([0])).mean()
            summary_parts.append(f"**Performance:** Total Requests: {total_requests:,.0f}, Avg Response Time: {avg_response:.3f}s")
        
        if energy_source == "ecofloc" and node_energy_data:
            total_energy = sum(df['energy_value'].sum() for df in node_energy_data)
            summary_parts.append(f"**Energy:** Total Consumption: {total_energy:.2f} Joules")
        
        summary_parts.append(f"**Filters Applied:** Node: {selected_node or 'All'}, Filter Type: {filter_type}")
        
        summary_info = html.Div([
            html.H5("Analysis Summary", style={"color": "#2c3e50", "marginBottom": "10px"}),
            html.Div([html.P(part) for part in summary_parts])
        ])
        
        return [fig_energy_node, fig_energy_comp, fig_transactions, fig_response, fig_process, fig_timeline, summary_info]
        
    except Exception as e:
        error_msg = f"Error in granular analysis: {str(e)}"
        empty = create_empty_figure(error_msg)
        error_info = html.Div([
            html.H5("Error", style={"color": "#e74c3c"}),
            html.P(error_msg, style={"color": "#e74c3c"})
        ])
        return [empty]*6 + [error_info]


# --- PROCESS ENERGY COMPARISON CALLBACKS (TAB 4) ---

# Populate process intensity dropdown
@app.callback(
    Output("process-intensity-dropdown", "options"),
    Input("process-component-dropdown", "value")
)
def populate_process_intensities(component):
    if not component: return []
    if component == 'all':
        # Get all intensities from all components
        all_intensities = set()
        for comp in ['cpu', 'ram', 'nic', 'sd']:
            all_intensities.update(data_loader.get_available_intensities(comp))
        return [{"label": i.upper(), "value": i} for i in sorted(all_intensities)] + [{"label": "ALL INTENSITIES", "value": "all"}]
    intensities = data_loader.get_available_intensities(component)
    return [{"label": i.upper(), "value": i} for i in intensities] + [{"label": "ALL INTENSITIES", "value": "all"}]

# Populate process experiment dropdown  
@app.callback(
    Output("process-experiment-dropdown", "options"),
    Output("process-experiment-dropdown", "value"),
    Input("process-component-dropdown", "value"),
    Input("process-intensity-dropdown", "value")
)
def populate_process_experiments(component, intensity):
    if not component or not intensity: return [], None
    
    all_experiments = []
    components_to_use = ['cpu', 'ram', 'nic', 'sd'] if component == 'all' else [component]
    
    for comp in components_to_use:
        if intensity == 'all':
            for intens in data_loader.get_available_intensities(comp):
                all_experiments.extend(data_loader.get_available_experiments(comp, intens))
        else:
            all_experiments.extend(data_loader.get_available_experiments(comp, intensity))
    
    unique_experiments = {exp['value']: exp for exp in all_experiments}.values()
    
    # Add ALL EXPERIMENTS option if multiple
    if len(list(unique_experiments)) > 1:
        options = [{"label": f"ALL EXPERIMENTS ({len(list(unique_experiments))} total)", "value": "all_experiments"}]
        options.extend([{"label": exp["label"], "value": exp["value"]} for exp in unique_experiments])
        return options, None
    
    return [{"label": exp["label"], "value": exp["value"]} for exp in unique_experiments], None

# Populate process name dropdown
@app.callback(
    Output("process-name-dropdown", "options"),
    Input("process-experiment-dropdown", "value"),
    Input("process-component-dropdown", "value"),
    Input("process-intensity-dropdown", "value")
)
def populate_process_names(experiment_path, component, intensity):
    if not experiment_path or not component or not intensity:
        return []
    
    try:
        # Get all unique process names from experiments
        all_processes = set()
        
        if experiment_path == "all_experiments":
            # Load from multiple experiments
            components_to_use = ['cpu', 'ram', 'nic', 'sd'] if component == 'all' else [component]
            for comp in components_to_use:
                intensities_to_use = data_loader.get_available_intensities(comp) if intensity == 'all' else [intensity]
                for intens in intensities_to_use:
                    for exp in data_loader.get_available_experiments(comp, intens):
                        pids_df = data_loader.load_informe_pids(exp['value'])
                        if not pids_df.empty and 'name_pid' in pids_df.columns:
                            all_processes.update(pids_df['name_pid'].unique())
        else:
            pids_df = data_loader.load_informe_pids(experiment_path)
            if not pids_df.empty and 'name_pid' in pids_df.columns:
                all_processes.update(pids_df['name_pid'].unique())
        
        return [{"label": proc, "value": proc} for proc in sorted(all_processes)]
    except Exception as e:
        print(f"Error loading process names: {e}")
        return []

# Main process analysis callback
@app.callback(
    Output("process-main-comparison-chart", "figure"),
    Output("process-node-chart-1", "figure"),
    Output("process-node-chart-2", "figure"),
    Output("process-node-chart-3", "figure"),
    Output("process-node-chart-4", "figure"),
    Output("process-component-breakdown-chart", "figure"),
    Output("process-heatmap-chart", "figure"),
    Output("process-summary-table", "children"),
    Input("btn-process-analysis", "n_clicks"),
    State("process-component-dropdown", "value"),
    State("process-intensity-dropdown", "value"),
    State("process-experiment-dropdown", "value"),
    State("process-name-dropdown", "value"),
    State("process-comparison-mode", "value")
)
def update_process_analysis(n_clicks, component, intensity, experiment_path, selected_processes, comparison_mode):
    if n_clicks == 0 or not component or not intensity:
        empty = create_empty_figure("Please select filters and click Generate Process Analysis")
        return [empty]*7 + ["Please configure filters above and click the Generate button."]
    
    try:
        # Collect experiments
        experiments_to_analyze = []
        components_to_use = ['cpu', 'ram', 'nic', 'sd'] if component == 'all' else [component]
        
        if experiment_path == "all_experiments" or not experiment_path:
            for comp in components_to_use:
                intensities_to_use = data_loader.get_available_intensities(comp) if intensity == 'all' else [intensity]
                for intens in intensities_to_use:
                    experiments_to_analyze.extend(data_loader.get_available_experiments(comp, intens))
            experiments_to_analyze = list({exp['value']: exp for exp in experiments_to_analyze}.values())
        else:
            experiments_to_analyze = [{'value': experiment_path, 'label': experiment_path}]
        
        if not experiments_to_analyze:
            empty = create_empty_figure("No experiments found")
            return [empty]*7 + ["No experiments found for the selected criteria."]
        
        # Collect all process energy data
        all_process_data = []
        all_component_data = []  # For component breakdown
        
        for exp in experiments_to_analyze:
            exp_path = exp['value']
            
            # Load PID mapping
            pids_df = data_loader.load_informe_pids(exp_path)
            if pids_df.empty:
                continue
            
            # Load energy data for each component
            for comp_type in ['cpu', 'ram', 'nic', 'sd']:
                pid_energy_df = data_loader.load_ecofloc_pid_data(exp_path, comp_type)
                if pid_energy_df.empty:
                    continue
                
                # Merge with process names
                merged = pid_energy_df.merge(pids_df, on=['node_name', 'pid'], how='inner')
                if merged.empty:
                    continue
                
                # Aggregate energy by process and node
                process_energy = merged.groupby(['node_name', 'name_pid'])['energy_value'].sum().reset_index()
                process_energy['component'] = comp_type.upper()
                process_energy['experiment'] = exp.get('label', exp_path)
                
                all_process_data.append(process_energy)
                all_component_data.append(process_energy.copy())
        
        if not all_process_data:
            empty = create_empty_figure("No process energy data found")
            return [empty]*7 + ["No process energy data found. Make sure experiments have informe_pids.csv and ecofloc data."]
        
        # Combine all data
        combined_df = pd.concat(all_process_data, ignore_index=True)
        
        # Filter by selected processes if specified
        if selected_processes and len(selected_processes) > 0:
            combined_df = combined_df[combined_df['name_pid'].isin(selected_processes)]
        
        if combined_df.empty:
            empty = create_empty_figure("No data for selected processes")
            return [empty]*7 + ["No data found for the selected processes."]
        
        # Get unique nodes
        nodes = sorted(combined_df['node_name'].unique())
        
        # --- 1. Main Comparison Chart ---
        if comparison_mode == "by_node":
            # Compare same processes across different nodes
            process_by_node = combined_df.groupby(['name_pid', 'node_name'])['energy_value'].mean().reset_index()
            fig_main = px.bar(
                process_by_node, x="name_pid", y="energy_value", color="node_name",
                barmode="group", title="Process Energy Comparison Across Nodes",
                labels={"energy_value": "Energy (Joules)", "name_pid": "Process", "node_name": "Node"}
            )
        elif comparison_mode == "by_component":
            # Show component breakdown per process
            process_by_comp = combined_df.groupby(['name_pid', 'component'])['energy_value'].mean().reset_index()
            fig_main = px.bar(
                process_by_comp, x="name_pid", y="energy_value", color="component",
                barmode="stack", title="Process Energy by Component",
                labels={"energy_value": "Energy (Joules)", "name_pid": "Process", "component": "Component"}
            )
        else:
            # Overview - top processes by total energy
            process_totals = combined_df.groupby('name_pid')['energy_value'].sum().reset_index()
            process_totals = process_totals.nlargest(20, 'energy_value')
            fig_main = px.bar(
                process_totals, x="name_pid", y="energy_value",
                title="Top 20 Energy-Consuming Processes (All Nodes)",
                labels={"energy_value": "Total Energy (Joules)", "name_pid": "Process"},
                color="energy_value", color_continuous_scale="Reds"
            )
        fig_main.update_layout(template="plotly_white", height=450)
        fig_main.update_xaxes(tickangle=45)
        
        # --- 2. Per-Node Pie Charts (up to 4 nodes) ---
        node_charts = []
        for i, node in enumerate(nodes[:4]):
            node_data = combined_df[combined_df['node_name'] == node]
            process_energy = node_data.groupby('name_pid')['energy_value'].sum().reset_index()
            # Get top 10 for readability
            process_energy = process_energy.nlargest(10, 'energy_value')
            
            fig_node = px.pie(
                process_energy, values="energy_value", names="name_pid",
                title=f"Energy Distribution - {node}", hole=0.4
            )
            fig_node.update_layout(template="plotly_white", height=350, showlegend=True)
            node_charts.append(fig_node)
        
        # Fill remaining with empty charts
        while len(node_charts) < 4:
            node_charts.append(create_empty_figure("No additional nodes"))
        
        # --- 3. Component Breakdown Chart ---
        comp_breakdown = combined_df.groupby(['name_pid', 'component'])['energy_value'].sum().reset_index()
        # Pivot for stacked visualization
        top_processes = combined_df.groupby('name_pid')['energy_value'].sum().nlargest(15).index
        comp_breakdown_filtered = comp_breakdown[comp_breakdown['name_pid'].isin(top_processes)]
        
        fig_comp = px.bar(
            comp_breakdown_filtered, x="name_pid", y="energy_value", color="component",
            barmode="stack", title="Component Energy Breakdown (Top 15 Processes)",
            labels={"energy_value": "Energy (Joules)", "name_pid": "Process"},
            color_discrete_map={"CPU": "#e74c3c", "RAM": "#3498db", "NIC": "#2ecc71", "SD": "#f39c12"}
        )
        fig_comp.update_layout(template="plotly_white", height=400)
        fig_comp.update_xaxes(tickangle=45)
        
        # --- 4. Heatmap ---
        # Create pivot table for heatmap
        heatmap_data = combined_df.groupby(['name_pid', 'node_name'])['energy_value'].sum().reset_index()
        heatmap_pivot = heatmap_data.pivot(index='name_pid', columns='node_name', values='energy_value').fillna(0)
        
        # Limit to top processes for readability
        top_procs = combined_df.groupby('name_pid')['energy_value'].sum().nlargest(20).index
        heatmap_pivot = heatmap_pivot[heatmap_pivot.index.isin(top_procs)]
        
        fig_heatmap = px.imshow(
            heatmap_pivot, 
            labels=dict(x="Node", y="Process", color="Energy (J)"),
            title="Process-Node Energy Heatmap (Top 20 Processes)",
            color_continuous_scale="YlOrRd",
            aspect="auto"
        )
        fig_heatmap.update_layout(template="plotly_white", height=500)
        
        # --- 5. Summary Table ---
        summary_stats = combined_df.groupby('name_pid').agg({
            'energy_value': ['sum', 'mean', 'std', 'count']
        }).reset_index()
        summary_stats.columns = ['Process', 'Total Energy (J)', 'Mean Energy (J)', 'Std Dev', 'Data Points']
        summary_stats = summary_stats.sort_values('Total Energy (J)', ascending=False).head(15)
        
        # Create HTML table
        table_rows = [html.Tr([html.Th(col) for col in summary_stats.columns])]
        for _, row in summary_stats.iterrows():
            table_rows.append(html.Tr([
                html.Td(row['Process']),
                html.Td(f"{row['Total Energy (J)']:.2f}"),
                html.Td(f"{row['Mean Energy (J)']:.4f}"),
                html.Td(f"{row['Std Dev']:.4f}" if pd.notna(row['Std Dev']) else "N/A"),
                html.Td(f"{int(row['Data Points'])}")
            ]))
        
        summary_table = html.Div([
            html.H5("Process Energy Summary (Top 15)", style={"color": "#2c3e50", "marginBottom": "10px"}),
            html.P(f"Total Experiments Analyzed: {len(experiments_to_analyze)} | Total Processes: {combined_df['name_pid'].nunique()} | Total Nodes: {len(nodes)}"),
            html.Table(table_rows, style={"width": "100%", "borderCollapse": "collapse", "marginTop": "10px"}),
        ])
        
        return [fig_main] + node_charts + [fig_comp, fig_heatmap, summary_table]
        
    except Exception as e:
        error_msg = f"Error in process analysis: {str(e)}"
        empty = create_empty_figure(error_msg)
        return [empty]*7 + [html.Div([html.H5("Error", style={"color": "#e74c3c"}), html.P(error_msg)])]


# --- SCHEDULER ANALYSIS CALLBACKS (TAB 5) ---

def extract_service_type(pod_name: str) -> str:
    """Extract service type from pod name: teastore-auth-xxx -> auth"""
    import re
    match = re.match(r'teastore-([a-z]+)-', pod_name)
    if match:
        return match.group(1)
    return pod_name

def load_scheduler_data():
    """Load the cleaned scheduler CSV data"""
    import os
    csv_path = os.path.join(os.path.dirname(__file__), 'teastore_scheduler_data_cleaned.csv')
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df['service_type'] = df['Pod'].apply(extract_service_type)
        # Simplify node names for better visualization
        df['node_short'] = df['Nodo'].apply(lambda x: x.replace('luish-', '').replace('-a315-55g', '').replace('-an515-57', ''))
        return df
    return pd.DataFrame()

@app.callback(
    Output("scheduler-node-distribution", "figure"),
    Output("scheduler-node-pie", "figure"),
    Output("scheduler-service-node-heatmap", "figure"),
    Output("scheduler-service-distribution", "figure"),
    Output("scheduler-temporal-distribution", "figure"),
    Output("scheduler-balance-boxplot", "figure"),
    Output("scheduler-balance-violin", "figure"),
    Output("scheduler-colocation-heatmap", "figure"),
    Output("scheduler-top-configurations", "figure"),
    Output("scheduler-summary-stats", "children"),
    Input("btn-scheduler-analysis", "n_clicks")
)
def update_scheduler_analysis(n_clicks):
    if n_clicks == 0:
        empty = create_empty_figure("Click 'Load Scheduler Data' to analyze")
        return [empty]*9 + ["Click the button above to load and analyze scheduler data."]
    
    try:
        df = load_scheduler_data()
        
        if df.empty:
            empty = create_empty_figure("No scheduler data found")
            return [empty]*9 + ["Could not find teastore_scheduler_data_cleaned.csv"]
        
        # Node color mapping for consistency
        node_colors = {
            'leo02': '#e74c3c',
            'aspire': '#3498db', 
            'nitro': '#2ecc71',
            'scorpius03': '#f39c12'
        }
        
        # --- 1. Overall Node Distribution ---
        node_counts = df['node_short'].value_counts().reset_index()
        node_counts.columns = ['Node', 'Count']
        
        fig_node_dist = px.bar(
            node_counts, x='Node', y='Count',
            title="Total Pod Assignments per Node",
            labels={"Count": "Number of Pod Assignments", "Node": "Node"},
            color='Node',
            color_discrete_map=node_colors
        )
        fig_node_dist.update_layout(template="plotly_white", showlegend=False)
        
        # Pie chart
        fig_node_pie = px.pie(
            node_counts, values='Count', names='Node',
            title="Pod Distribution Share by Node",
            color='Node',
            color_discrete_map=node_colors,
            hole=0.4
        )
        fig_node_pie.update_layout(template="plotly_white")
        
        # --- 2. Service-Node Heatmap ---
        service_node_counts = df.groupby(['service_type', 'node_short']).size().reset_index(name='count')
        heatmap_pivot = service_node_counts.pivot(index='service_type', columns='node_short', values='count').fillna(0)
        
        fig_heatmap = px.imshow(
            heatmap_pivot,
            labels=dict(x="Node", y="Service", color="Assignments"),
            title="Service-Node Assignment Frequency",
            color_continuous_scale="YlOrRd",
            aspect="auto",
            text_auto=True
        )
        fig_heatmap.update_layout(template="plotly_white", height=400)
        
        # --- 3. Per-Service Distribution (Stacked Bar - Normalized) ---
        # Calculate percentage for each service
        service_node_pct = service_node_counts.copy()
        service_totals = service_node_pct.groupby('service_type')['count'].transform('sum')
        service_node_pct['percentage'] = (service_node_pct['count'] / service_totals * 100).round(1)
        
        fig_service_dist = px.bar(
            service_node_pct, x='service_type', y='percentage', color='node_short',
            title="Node Preference by Service Type (Percentage)",
            labels={"percentage": "% of Assignments", "service_type": "Service", "node_short": "Node"},
            color_discrete_map=node_colors,
            barmode='stack',
            text='percentage'
        )
        fig_service_dist.update_layout(template="plotly_white", height=400)
        fig_service_dist.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
        
        # --- 4. Temporal Distribution (Pods per node over iterations) ---
        # Group iterations into windows of 50 for cleaner visualization
        df['iteration_window'] = (df['Iteracion'] // 50) * 50
        temporal_counts = df.groupby(['iteration_window', 'node_short']).size().reset_index(name='pod_count')
        
        fig_temporal = px.line(
            temporal_counts, x='iteration_window', y='pod_count', color='node_short',
            title="Pod Assignments per Node Over Time (50-iteration windows)",
            labels={"iteration_window": "Iteration Window", "pod_count": "Number of Pods", "node_short": "Node"},
            color_discrete_map=node_colors,
            markers=True
        )
        fig_temporal.update_layout(template="plotly_white", height=400)
        
        # --- 5. Node Balance Analysis ---
        # Count pods per node per iteration
        balance_df = df.groupby(['Iteracion', 'node_short']).size().reset_index(name='pod_count')
        
        fig_boxplot = px.box(
            balance_df, x='node_short', y='pod_count', color='node_short',
            title="Pod Count Distribution per Node (per iteration)",
            labels={"pod_count": "Pods per Iteration", "node_short": "Node"},
            color_discrete_map=node_colors
        )
        fig_boxplot.update_layout(template="plotly_white", showlegend=False)
        
        fig_violin = px.violin(
            balance_df, x='node_short', y='pod_count', color='node_short',
            title="Pod Count Density per Node",
            labels={"pod_count": "Pods per Iteration", "node_short": "Node"},
            color_discrete_map=node_colors,
            box=True
        )
        fig_violin.update_layout(template="plotly_white", showlegend=False)
        
        # --- 6. Co-location Patterns ---
        # For each iteration, which services share the same node?
        colocation_matrix = pd.DataFrame(0, 
            index=df['service_type'].unique(), 
            columns=df['service_type'].unique(),
            dtype=float
        )
        
        for iteracion in df['Iteracion'].unique():
            iter_df = df[df['Iteracion'] == iteracion]
            for node in iter_df['node_short'].unique():
                services_on_node = iter_df[iter_df['node_short'] == node]['service_type'].tolist()
                for s1 in services_on_node:
                    for s2 in services_on_node:
                        colocation_matrix.loc[s1, s2] += 1
        
        # Normalize by total iterations
        colocation_matrix = colocation_matrix / df['Iteracion'].nunique()
        
        fig_colocation = px.imshow(
            colocation_matrix,
            labels=dict(x="Service", y="Service", color="Co-location Rate"),
            title="Service Co-location Frequency (avg times per iteration on same node)",
            color_continuous_scale="Blues",
            aspect="auto",
            text_auto='.2f'
        )
        fig_colocation.update_layout(template="plotly_white", height=450)
        
        # --- 7. Most Common Configurations ---
        # Create a configuration string for each iteration
        def get_config(group):
            return '|'.join([f"{row['service_type']}:{row['node_short']}" for _, row in group.sort_values('service_type').iterrows()])
        
        configs = df.groupby('Iteracion').apply(get_config).reset_index(name='configuration')
        config_counts = configs['configuration'].value_counts().head(15).reset_index()
        config_counts.columns = ['Configuration', 'Count']
        
        # Simplify configuration display
        config_counts['Config_Short'] = config_counts['Configuration'].apply(
            lambda x: '<br>'.join([item.replace(':', '→') for item in x.split('|')])
        )
        config_counts['Config_ID'] = [f"Config #{i+1}" for i in range(len(config_counts))]
        
        fig_configs = px.bar(
            config_counts, x='Config_ID', y='Count',
            title="Top 15 Most Common Pod-Node Configurations",
            labels={"Count": "Occurrences", "Config_ID": "Configuration"},
            color='Count',
            color_continuous_scale="Viridis",
            hover_data={'Config_Short': True}
        )
        fig_configs.update_layout(template="plotly_white", height=400)
        
        # --- Summary Statistics ---
        total_iterations = df['Iteracion'].nunique()
        total_assignments = len(df)
        nodes = df['node_short'].unique()
        
        # Calculate preference scores
        node_prefs = df.groupby('node_short').size() / total_assignments * 100
        
        # Most imbalanced iterations
        iter_balance = balance_df.groupby('Iteracion')['pod_count'].agg(['min', 'max', 'std'])
        most_balanced = iter_balance.nsmallest(5, 'std').index.tolist()
        most_imbalanced = iter_balance.nlargest(5, 'std').index.tolist()
        
        # Service preferences
        service_prefs = df.groupby('service_type')['node_short'].agg(lambda x: x.value_counts().index[0])
        
        summary_html = html.Div([
            html.H5("Scheduler Analysis Summary", style={"color": "#2c3e50", "marginBottom": "15px"}),
            
            html.Div([
                html.Div([
                    html.H6("📊 General Statistics", style={"color": "#16a085"}),
                    html.P(f"Total Iterations Analyzed: {total_iterations:,}"),
                    html.P(f"Total Pod Assignments: {total_assignments:,}"),
                    html.P(f"Unique Nodes: {len(nodes)} ({', '.join(nodes)})"),
                ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top", "paddingRight": "20px"}),
                
                html.Div([
                    html.H6("🎯 Node Preference Ranking", style={"color": "#e74c3c"}),
                    html.Ul([html.Li(f"{node}: {pct:.1f}%") for node, pct in node_prefs.sort_values(ascending=False).items()])
                ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top", "paddingRight": "20px"}),
                
                html.Div([
                    html.H6("🔗 Service → Preferred Node", style={"color": "#3498db"}),
                    html.Ul([html.Li(f"{svc}: {node}") for svc, node in service_prefs.items()])
                ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top"}),
            ], style={"marginBottom": "20px"}),
            
            html.Div([
                html.H6("⚖️ Balance Insights", style={"color": "#9b59b6"}),
                html.P(f"Most Balanced Iterations (lowest std): {most_balanced}"),
                html.P(f"Most Imbalanced Iterations (highest std): {most_imbalanced}"),
                html.P(f"Unique configurations found: {config_counts['Configuration'].nunique()} (showing top 15)"),
            ])
        ])
        
        return [
            fig_node_dist, fig_node_pie, fig_heatmap, fig_service_dist,
            fig_temporal, fig_boxplot, fig_violin, fig_colocation,
            fig_configs, summary_html
        ]
        
    except Exception as e:
        error_msg = f"Error in scheduler analysis: {str(e)}"
        empty = create_empty_figure(error_msg)
        return [empty]*9 + [html.Div([html.H5("Error", style={"color": "#e74c3c"}), html.P(error_msg)])]


# --- TAB 6: Energy Score Manager Callback ---

@app.callback(
    Output("energy-k8s-nodes-table", "figure"),
    Output("energy-scores-bar-chart", "figure"),
    Output("energy-component-breakdown", "figure"),
    Output("energy-efficiency-radar", "figure"),
    Output("energy-score-weights", "figure"),
    Output("energy-score-ranking", "figure"),
    Output("energy-score-summary", "children"),
    Output("energy-score-status", "children"),
    Input("btn-calculate-energy-scores", "n_clicks"),
    Input("btn-apply-energy-scores", "n_clicks"),
    State("energy-score-source", "value")
)
def update_energy_scores(calc_clicks, apply_clicks, energy_source):
    """Callback para calcular y aplicar Energy Scores a Kubernetes"""
    import subprocess
    import json
    from dash import ctx
    
    empty = create_empty_figure("Haz clic en 'Calcular Scores' para comenzar")
    
    if calc_clicks == 0 and apply_clicks == 0:
        return [empty]*6 + [
            html.Div("Selecciona la fuente de energía y haz clic en 'Calcular Scores'"),
            html.Div()
        ]
    
    try:
        # Determinar qué botón fue presionado
        triggered_id = ctx.triggered_id
        should_apply = triggered_id == "btn-apply-energy-scores"
        
        status_msg = html.Div()
        
        # 1. Obtener nodos activos de Kubernetes
        result = subprocess.run(
            ["kubectl", "get", "nodes", "-o", "json"],
            capture_output=True, text=True, check=True
        )
        nodes_data = json.loads(result.stdout)
        
        k8s_nodes = []
        for item in nodes_data.get("items", []):
            node_name = item["metadata"]["name"]
            labels = item["metadata"].get("labels", {})
            current_score = labels.get("energy-score", "N/A")
            
            status = "Unknown"
            for condition in item.get("status", {}).get("conditions", []):
                if condition["type"] == "Ready":
                    status = "Ready" if condition["status"] == "True" else "NotReady"
                    break
            
            # Obtener IP
            ip = "Unknown"
            for addr in item.get("status", {}).get("addresses", []):
                if addr.get("type") == "InternalIP":
                    ip = addr.get("address", "Unknown")
                    break
            
            k8s_nodes.append({
                "name": node_name,
                "status": status,
                "ip": ip,
                "current_score": current_score
            })
        
        # Crear tabla de nodos K8s
        fig_nodes_table = go.Figure(data=[go.Table(
            header=dict(
                values=['<b>Nodo</b>', '<b>Estado</b>', '<b>IP</b>', '<b>Score Actual</b>'],
                fill_color='#3498db',
                font=dict(color='white', size=12),
                align='left'
            ),
            cells=dict(
                values=[
                    [n['name'] for n in k8s_nodes],
                    [n['status'] for n in k8s_nodes],
                    [n['ip'] for n in k8s_nodes],
                    [n['current_score'] for n in k8s_nodes]
                ],
                fill_color=[['#ecf0f1', 'white'] * len(k8s_nodes)],
                align='left'
            )
        )])
        fig_nodes_table.update_layout(
            title="Nodos Kubernetes Activos",
            height=300,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        
        # 2. Recolectar datos de energía
        all_energy_data = []
        node_component_totals = {}
        
        # Mapeo de nombres (igual que en energy_score_labeler.py)
        NODE_NAME_MAPPING = {
            "aspire": "luish-aspire-a315-55g",
            "nitro5": "luish-nitro-an515-57",
            "nitro": "luish-nitro-an515-57",
        }
        
        # Pesos de componentes
        COMPONENT_WEIGHTS = {"cpu": 0.35, "ram": 0.15, "nic": 0.25, "sd": 0.25}
        
        if energy_source == "ecofloc":
            for component in ['cpu', 'ram', 'nic', 'sd', 'unified']:
                intensities = data_loader.get_available_intensities(component)
                for intensity in intensities:
                    experiments = data_loader.get_available_experiments(component, intensity)
                    for exp in experiments:
                        for comp_type in ['cpu', 'ram', 'sd', 'nic']:
                            df = data_loader.load_ecofloc_component_data(exp['value'], comp_type)
                            if not df.empty:
                                totals = df.groupby('node_name')['energy_value'].sum().reset_index()
                                totals['component'] = comp_type
                                all_energy_data.append(totals)
        else:  # scaphandre
            for component in data_loader.get_available_components():
                intensities = data_loader.get_available_intensities(component)
                for intensity in intensities:
                    experiments = data_loader.get_available_experiments(component, intensity)
                    for exp in experiments:
                        df = data_loader.load_scaphandre_data(exp['value'])
                        if not df.empty:
                            totals = df.groupby('node_name')['energy_value'].sum().reset_index()
                            totals['component'] = 'global'
                            all_energy_data.append(totals)
        
        if not all_energy_data:
            return [empty]*6 + [
                html.Div([
                    html.H5("Sin Datos", style={"color": "#e74c3c"}),
                    html.P(f"No se encontraron datos de energía para {energy_source}")
                ]),
                html.Div("❌ No hay datos de energía disponibles", style={"color": "#e74c3c"})
            ]
        
        combined_energy = pd.concat(all_energy_data, ignore_index=True)
        avg_energy = combined_energy.groupby(['node_name', 'component'])['energy_value'].mean().reset_index()
        
        # 3. Calcular scores
        scores = {}
        nodes_in_data = avg_energy['node_name'].unique()
        
        for node in nodes_in_data:
            node_data = avg_energy[avg_energy['node_name'] == node]
            component_scores = {}
            
            for comp in ['cpu', 'ram', 'nic', 'sd'] if energy_source == "ecofloc" else ['global']:
                comp_data = avg_energy[avg_energy['component'] == comp]
                if comp_data.empty:
                    continue
                
                node_comp = comp_data[comp_data['node_name'] == node]
                if node_comp.empty:
                    continue
                
                value = node_comp['energy_value'].values[0]
                min_val = comp_data['energy_value'].min()
                max_val = comp_data['energy_value'].max()
                
                # Invertido: menor consumo = mayor score
                if max_val > min_val:
                    normalized = 100 - ((value - min_val) / (max_val - min_val)) * 100
                else:
                    normalized = 50.0
                
                component_scores[comp] = normalized
            
            # Score ponderado
            if energy_source == "ecofloc" and component_scores:
                total = sum(component_scores.get(c, 50) * COMPONENT_WEIGHTS.get(c, 0.25) 
                           for c in COMPONENT_WEIGHTS)
                scores[node] = round(total, 2)
            elif component_scores:
                scores[node] = round(component_scores.get('global', 50), 2)
        
        # 4. Gráfico de barras de scores
        score_df = pd.DataFrame([
            {"node": n, "score": s, "efficiency": "⚡ Alta" if s >= 70 else ("📊 Media" if s >= 40 else "🔥 Baja")}
            for n, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)
        ])
        
        colors = ['#27ae60' if s >= 70 else '#f39c12' if s >= 40 else '#e74c3c' for s in score_df['score']]
        
        fig_scores = go.Figure(data=[go.Bar(
            x=score_df['node'],
            y=score_df['score'],
            marker_color=colors,
            text=[f"{s:.1f}" for s in score_df['score']],
            textposition='auto'
        )])
        fig_scores.update_layout(
            title=f"Energy Scores Calculados ({energy_source.upper()})",
            xaxis_title="Nodo",
            yaxis_title="Score (0-100, mayor=mejor)",
            template="plotly_white",
            height=300
        )
        
        # 5. Desglose por componente
        if energy_source == "ecofloc":
            fig_breakdown = px.bar(
                avg_energy, x="node_name", y="energy_value", color="component",
                barmode="group",
                title="Consumo Promedio por Componente y Nodo",
                labels={"energy_value": "Energía (Joules)", "node_name": "Nodo"},
                color_discrete_map={"cpu": "#e74c3c", "ram": "#3498db", "nic": "#2ecc71", "sd": "#9b59b6"}
            )
        else:
            fig_breakdown = px.bar(
                avg_energy, x="node_name", y="energy_value",
                title="Consumo Promedio Scaphandre por Nodo",
                labels={"energy_value": "Energía (Watts)", "node_name": "Nodo"},
                color_discrete_sequence=['#e67e22']
            )
        fig_breakdown.update_layout(template="plotly_white", height=350)
        
        # 6. Gráfico radar de eficiencia (solo para ecofloc)
        if energy_source == "ecofloc" and len(scores) > 0:
            # Crear scores por componente para cada nodo
            radar_data = []
            for node in scores.keys():
                node_data = avg_energy[avg_energy['node_name'] == node]
                for comp in ['cpu', 'ram', 'nic', 'sd']:
                    comp_data = avg_energy[avg_energy['component'] == comp]
                    node_comp = comp_data[comp_data['node_name'] == node]
                    if not node_comp.empty:
                        value = node_comp['energy_value'].values[0]
                        min_val = comp_data['energy_value'].min()
                        max_val = comp_data['energy_value'].max()
                        if max_val > min_val:
                            score = 100 - ((value - min_val) / (max_val - min_val)) * 100
                        else:
                            score = 50.0
                        radar_data.append({"node": node, "component": comp.upper(), "score": score})
            
            radar_df = pd.DataFrame(radar_data)
            fig_radar = px.line_polar(
                radar_df, r="score", theta="component", color="node",
                line_close=True,
                title="Eficiencia por Componente (Radar)"
            )
            fig_radar.update_traces(fill='toself', opacity=0.5)
            fig_radar.update_layout(height=350)
        else:
            fig_radar = create_empty_figure("Radar solo disponible para Ecofloc")
        
        # 7. Gráfico de pesos
        fig_weights = px.pie(
            values=list(COMPONENT_WEIGHTS.values()),
            names=[k.upper() for k in COMPONENT_WEIGHTS.keys()],
            title="Pesos de Componentes para el Cálculo",
            hole=0.4,
            color_discrete_sequence=['#e74c3c', '#3498db', '#2ecc71', '#9b59b6']
        )
        fig_weights.update_layout(height=350)
        
        # 8. Ranking de scores
        fig_ranking = go.Figure(data=[go.Bar(
            y=[f"#{i+1} {n}" for i, (n, s) in enumerate(sorted(scores.items(), key=lambda x: x[1], reverse=True))],
            x=[s for n, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)],
            orientation='h',
            marker_color=['#27ae60' if s >= 70 else '#f39c12' if s >= 40 else '#e74c3c' 
                         for n, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)],
            text=[f"{s:.2f}" for n, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)],
            textposition='auto'
        )])
        fig_ranking.update_layout(
            title="Ranking de Eficiencia Energética",
            xaxis_title="Score",
            yaxis_title="Nodo",
            template="plotly_white",
            height=350
        )
        
        # 9. Mapear a nodos K8s
        k8s_node_names = [n['name'] for n in k8s_nodes]
        node_score_mapping = {}
        
        for data_node, score in scores.items():
            # Mapeo manual primero
            if data_node in NODE_NAME_MAPPING:
                k8s_name = NODE_NAME_MAPPING[data_node]
                if k8s_name in k8s_node_names:
                    node_score_mapping[k8s_name] = score
                    continue
            
            # Buscar coincidencia
            for k8s_name in k8s_node_names:
                data_norm = data_node.lower().replace('_', '-')
                k8s_norm = k8s_name.lower()
                if data_norm == k8s_norm or data_norm in k8s_norm or k8s_norm in data_norm:
                    node_score_mapping[k8s_name] = score
                    break
        
        # Nodos sin datos
        for n in k8s_nodes:
            if n['name'] not in node_score_mapping:
                node_score_mapping[n['name']] = 50.0
        
        # 10. Si se pidió aplicar, ejecutar kubectl
        if should_apply:
            apply_results = []
            for node_name, score in node_score_mapping.items():
                try:
                    cmd = ["kubectl", "label", "nodes", node_name, f"energy-score={score:.2f}", "--overwrite"]
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    apply_results.append(f"✓ {node_name}: {score:.2f}")
                except subprocess.CalledProcessError as e:
                    apply_results.append(f"✗ {node_name}: Error - {e.stderr}")
            
            status_msg = html.Div([
                html.H5("🚀 Labels Aplicados", style={"color": "#27ae60"}),
                html.Ul([html.Li(r) for r in apply_results])
            ], style={"backgroundColor": "#d4edda", "padding": "15px", "borderRadius": "5px"})
        else:
            status_msg = html.Div([
                html.H5("🧮 Scores Calculados", style={"color": "#3498db"}),
                html.P("Haz clic en 'Aplicar a Kubernetes' para actualizar los labels.")
            ], style={"backgroundColor": "#cce5ff", "padding": "15px", "borderRadius": "5px"})
        
        # 11. Resumen
        summary = html.Div([
            html.H5("Resumen de Energy Scores", style={"color": "#2c3e50", "marginBottom": "15px"}),
            
            html.Div([
                html.Div([
                    html.H6("📊 Estadísticas", style={"color": "#16a085"}),
                    html.P(f"Fuente de datos: {energy_source.upper()}"),
                    html.P(f"Nodos con datos: {len(scores)}"),
                    html.P(f"Nodos K8s activos: {len(k8s_nodes)}"),
                    html.P(f"Score promedio: {sum(scores.values())/len(scores):.2f}" if scores else "N/A"),
                ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top", "paddingRight": "20px"}),
                
                html.Div([
                    html.H6("🏆 Ranking", style={"color": "#e74c3c"}),
                    html.Ul([
                        html.Li(f"{n}: {s:.2f} {'⚡' if s >= 70 else '📊' if s >= 40 else '🔥'}")
                        for n, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
                    ])
                ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top", "paddingRight": "20px"}),
                
                html.Div([
                    html.H6("💻 Comandos kubectl", style={"color": "#3498db"}),
                    html.Pre(
                        "\n".join([f"kubectl label nodes {n} energy-score={s:.2f} --overwrite" 
                                  for n, s in node_score_mapping.items()]),
                        style={"backgroundColor": "#2c3e50", "color": "#ecf0f1", "padding": "10px", 
                               "borderRadius": "5px", "fontSize": "11px", "overflowX": "auto"}
                    )
                ], style={"width": "38%", "display": "inline-block", "verticalAlign": "top"}),
            ])
        ])
        
        return [fig_nodes_table, fig_scores, fig_breakdown, fig_radar, fig_weights, fig_ranking, summary, status_msg]
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        empty = create_empty_figure(error_msg)
        return [empty]*6 + [
            html.Div([html.H5("Error", style={"color": "#e74c3c"}), html.P(str(e))]),
            html.Div(f"❌ {error_msg}", style={"color": "#e74c3c"})
        ]


if __name__ == "__main__":
    app.run(debug=True, port=8051)