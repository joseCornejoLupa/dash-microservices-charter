"""
Test script for the new enhancements
"""
import sys
sys.path.insert(0, '/home/josec/green_computing/microservices/historyexecutions/experiments-data/m_dash_dashboard')

from data_loader import DataLoader
import pandas as pd

ROOT_DIR = "/home/josec/green_computing/microservices/historyexecutions/experiments-data"
data_loader = DataLoader(ROOT_DIR)

# Test with an experiment that has informe_pids.csv
test_experiment_path = "/home/josec/green_computing/microservices/historyexecutions/experiments-data/por-componentes/cpu/low/ejecucion(08:30:03)cpulow"

print("=" * 60)
print("Testing Enhanced Data Loading Functions")
print("=" * 60)

# Test 1: Load informe_pids.csv
print("\nTest 1: Loading informe_pids.csv...")
pids_df = data_loader.load_informe_pids(test_experiment_path)
print(f"Shape: {pids_df.shape}")
print(f"Columns: {list(pids_df.columns)}")
print(f"Sample data:\n{pids_df.head(10)}")

# Test 2: Load per-PID energy data
print("\n\nTest 2: Loading per-PID energy data...")
pid_energy_df = data_loader.load_ecofloc_pid_data(test_experiment_path, 'cpu')
print(f"Shape: {pid_energy_df.shape}")
print(f"Columns: {list(pid_energy_df.columns)}")
print(f"Sample data:\n{pid_energy_df.head(10)}")
print(f"Unique PIDs: {pid_energy_df['pid'].nunique()}")
print(f"Unique nodes: {pid_energy_df['node_name'].unique()}")

# Test 3: Merge and aggregate
print("\n\nTest 3: Merging and aggregating data...")
if not pids_df.empty and not pid_energy_df.empty:
    merged_df = pid_energy_df.merge(
        pids_df,
        on=['node_name', 'pid'],
        how='inner'
    )
    print(f"Merged shape: {merged_df.shape}")
    print(f"Sample merged data:\n{merged_df.head(10)}")

    # Aggregate
    aggregated = merged_df.groupby(['node_name', 'name_pid'])['energy_value'].sum().reset_index()
    aggregated = aggregated.sort_values('energy_value', ascending=False)
    print(f"\nTop 10 energy-consuming processes:")
    print(aggregated.head(10))
else:
    print("Cannot merge - one or both DataFrames are empty")

# Test 4: Load both energy sources
print("\n\nTest 4: Loading both energy sources for comparison...")
ecofloc_df = data_loader.load_ecofloc_data(test_experiment_path, 'cpu')
scaphandre_df = data_loader.load_scaphandre_data(test_experiment_path)
print(f"Ecofloc shape: {ecofloc_df.shape}")
print(f"Scaphandre shape: {scaphandre_df.shape}")
print(f"Ecofloc nodes: {ecofloc_df['node_name'].unique() if not ecofloc_df.empty else 'No data'}")
print(f"Scaphandre nodes: {scaphandre_df['node_name'].unique() if not scaphandre_df.empty else 'No data'}")

print("\n" + "=" * 60)
print("Tests completed!")
print("=" * 60)
