# Multi-Tabbed Dash Dashboard for Experimental Data Analysis

A sophisticated Plotly Dash application for analyzing experimental data with energy-efficient design principles.

## Features

### Control Panel
- Filter by Component: cpu, ram, nic, sd, unified
- Filter by Intensity: low, med, high
- Select Experiment: Dynamically populated based on filters

### Tab 1: Energy Analysis
- **Energy Source Selection**: Choose between Ecofloc or Scaphandre data
- **Charts**:
  1. Energy Evolution: Time-series line chart showing energy consumption per node
  2. Energy Distribution by Node: Pie chart showing energy distribution across nodes
  3. Cumulative Energy per Node: Horizontal bar chart with color-coded energy totals

### Tab 2: Benchmark Performance
- **Charts**:
  1. Transaction Status: Multi-line chart showing successful/failed/dropped transactions over time
  2. Average Response Time: Area chart displaying response time trends
  3. Load Intensity: Time-series showing load intensity progression

## Installation

1. Navigate to the dashboard directory:
```bash
cd /home/josec/green_computing/microservices/historyexecutions/experiments-data/m_dash_dashboard
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://127.0.0.1:8050
```

3. Use the control panel:
   - Select a Component (cpu, ram, nic, sd, or unified)
   - Select an Intensity level (low, med, high)
   - Choose an Experiment from the dropdown
   - Data will load automatically after experiment selection

4. Navigate between tabs to view different analyses

## Energy Efficiency Features

- **On-Demand Loading**: Data is loaded only when an experiment is selected
- **Efficient Operations**: Uses optimized Pandas operations
- **No Pre-loading**: Minimal memory footprint

## Data Structure

The application expects the following directory structure:

```
por-componentes/
├── cpu/
│   ├── low/
│   │   └── ejecucion(...)/
│   ├── med/
│   │   └── ejecucion(...)/
│   └── high/
│       └── ejecucion(...)/
├── ram/
├── nic/
├── sd/
└── unified/
```

Each experiment directory should contain:
- `clean_results/ecofloc/` (preferred) or `raw_results/ecofloc/`
- `raw_results/scaphandre/`
- `raw_results/limbo/`

## File Formats

### Ecofloc Files
- Location: `clean_results/ecofloc/` or `raw_results/ecofloc/`
- Pattern: `ecofloc_<node_name>_<component>.txt`
- Format: CSV with timestamp, value1, value2

### Scaphandre Files
- Location: `raw_results/scaphandre/`
- Pattern: `scaph_<node_name>.txt`
- Format: Text with "X s: Y.YYW, Z.ZZJ, total=T.TTJ"

### Limbo Files
- Location: `raw_results/limbo/`
- Pattern: `limbo_results_teastore_<intensity>.csv`
- Format: Standard CSV with benchmark metrics

## Technical Details

- **Framework**: Plotly Dash 2.14.0+
- **Visualization**: Plotly 5.17.0+
- **Data Processing**: Pandas 2.1.0+
- **Port**: 8050 (default)
- **Host**: 0.0.0.0 (accessible from network)

## Troubleshooting

If data doesn't appear:
1. Check that the experiment directory exists
2. Verify that data files are in `clean_results/` or `raw_results/`
3. Check the console for error messages
4. Ensure file naming matches expected patterns

## File Structure

```
m_dash_dashboard/
├── app.py              # Main Dash application
├── data_loader.py      # Data loading utilities
├── requirements.txt    # Python dependencies
└── README.md          # This file
```
