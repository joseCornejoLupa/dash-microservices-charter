"""
Data Loading Utilities for Multi-Tabbed Dash Application
Handles loading of Ecofloc, Scaphandre, and Limbo data files
"""

import os
import pandas as pd
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import re


class DataLoader:
    """Main data loader class for experimental data"""

    def __init__(self, root_dir: str):
        """
        Initialize the data loader

        Args:
            root_dir: Root directory containing 'por-componentes' folder
        """
        self.root_dir = Path(root_dir)
        self.por_componentes_dir = self.root_dir / 'por-componentes'

    def get_available_components(self) -> List[str]:
        """Get list of available components"""
        components = []
        if self.por_componentes_dir.exists():
            components = [d.name for d in self.por_componentes_dir.iterdir()
                         if d.is_dir() and d.name in ['cpu', 'ram', 'nic', 'sd', 'unified']]
        return sorted(components)

    def get_available_intensities(self, component: str) -> List[str]:
        """Get list of available intensities for a component"""
        component_dir = self.por_componentes_dir / component
        if not component_dir.exists():
            return []

        intensities = []
        for d in component_dir.iterdir():
            if d.is_dir() and d.name in ['low', 'med', 'high']:
                intensities.append(d.name)
        return sorted(intensities)

    def get_available_experiments(self, component: str, intensity: str) -> List[Dict[str, str]]:
        """
        Get list of available experiments for a component and intensity

        Returns:
            List of dicts with 'label' and 'value' (full path)
        """
        intensity_dir = self.por_componentes_dir / component / intensity
        if not intensity_dir.exists():
            return []

        experiments = []
        for d in intensity_dir.iterdir():
            if d.is_dir() and d.name.startswith('ejecucion'):
                experiments.append({
                    'label': d.name,
                    'value': str(d)
                })
        return sorted(experiments, key=lambda x: x['label'])

    def load_ecofloc_data(self, experiment_path: str, component: str) -> pd.DataFrame:
        """
        Load Ecofloc data from clean_results or raw_results

        Args:
            experiment_path: Full path to experiment directory
            component: Component name (cpu, ram, nic, sd, unified)

        Returns:
            DataFrame with columns: node_name, timestamp, energy_value
        """
        exp_path = Path(experiment_path)

        # Priority: clean_results first, then raw_results
        search_dirs = [
            exp_path / 'clean_results' / 'ecofloc',
            exp_path / 'raw_results' / 'ecofloc'
        ]

        all_data = []

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # Find all ecofloc files
            for file_path in search_dir.glob('ecofloc_*.txt'):
                # Extract node name from filename: ecofloc_<node_name>_<component>.txt
                filename = file_path.name
                match = re.match(r'ecofloc_([^_]+)_(.+)\.txt', filename)
                if not match:
                    continue

                node_name = match.group(1)
                file_component = match.group(2)

                # For unified, load all components; otherwise, match component
                if component != 'unified' and file_component != component:
                    continue

                try:
                    # Read the file, skip the first 2 lines (summary lines)
                    with open(file_path, 'r') as f:
                        lines = f.readlines()

                    # Skip header lines that start with "Average" or "Total"
                    data_lines = [line for line in lines
                                 if not line.startswith('Average')
                                 and not line.startswith('Total')
                                 and line.strip()]

                    if not data_lines:
                        continue

                    # Parse CSV data: timestamp,value1,value2
                    rows = []
                    for line in data_lines:
                        parts = line.strip().split(',')
                        if len(parts) >= 3:
                            timestamp = parts[0]
                            energy_value = float(parts[2])  # Column 3 (index 2)
                            rows.append({
                                'node_name': node_name,
                                'timestamp': pd.to_datetime(timestamp),
                                'energy_value': energy_value
                            })

                    if rows:
                        all_data.extend(rows)

                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
                    continue

            # If we found data in clean_results, don't check raw_results
            if all_data:
                break

        if not all_data:
            return pd.DataFrame(columns=['node_name', 'timestamp', 'energy_value'])

        df = pd.DataFrame(all_data)
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Calculate elapsed seconds from first timestamp
        if not df.empty and 'timestamp' in df.columns:
            min_timestamp = df['timestamp'].min()
            df['elapsed_seconds'] = (df['timestamp'] - min_timestamp).dt.total_seconds()

        return df

    def load_scaphandre_data(self, experiment_path: str) -> pd.DataFrame:
        """
        Load Scaphandre data from raw_results/scaphandre

        Args:
            experiment_path: Full path to experiment directory

        Returns:
            DataFrame with columns: node_name, timestamp, energy_value
        """
        exp_path = Path(experiment_path)
        scaph_dir = exp_path / 'raw_results' / 'scaphandre'

        if not scaph_dir.exists():
            return pd.DataFrame(columns=['node_name', 'timestamp', 'energy_value'])

        all_data = []

        # Find all scaphandre files: scaph_<node_name>.txt
        for file_path in scaph_dir.glob('scaph_*.txt'):
            filename = file_path.name
            match = re.match(r'scaph_([^.]+)\.txt', filename)
            if not match:
                continue

            node_name = match.group(1)

            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()

                # Parse lines: "X s: Y.YYW, Z.ZZJ, total=T.TTJ"
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('Total Energy'):
                        continue

                    # Extract timestamp (seconds) and power (Watts)
                    match = re.match(r'(\d+)\s+s:\s+([\d.]+)W', line)
                    if match:
                        seconds = int(match.group(1))
                        power_watts = float(match.group(2))

                        all_data.append({
                            'node_name': node_name,
                            'timestamp': seconds,
                            'energy_value': power_watts
                        })

            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                continue

        if not all_data:
            return pd.DataFrame(columns=['node_name', 'timestamp', 'energy_value'])

        df = pd.DataFrame(all_data)
        df = df.sort_values(['node_name', 'timestamp']).reset_index(drop=True)

        # Calculate elapsed seconds from first timestamp (already in seconds for scaphandre)
        if not df.empty and 'timestamp' in df.columns:
            min_timestamp = df['timestamp'].min()
            df['elapsed_seconds'] = df['timestamp'] - min_timestamp

        return df

    def load_limbo_data(self, experiment_path: str, intensity: str) -> pd.DataFrame:
        """
        Load Limbo benchmark data

        Args:
            experiment_path: Full path to experiment directory
            intensity: Intensity level (low, med, high)

        Returns:
            DataFrame with benchmark data
        """
        exp_path = Path(experiment_path)
        limbo_dir = exp_path / 'raw_results' / 'limbo'

        if not limbo_dir.exists():
            return pd.DataFrame()

        # Map intensity to file naming convention
        intensity_map = {
            'low': 'low',
            'med': 'medium',
            'high': 'high'
        }

        file_intensity = intensity_map.get(intensity, intensity)
        limbo_file = limbo_dir / f'limbo_results_teastore_{file_intensity}.csv'

        if not limbo_file.exists():
            # Try alternative naming
            for alt_file in limbo_dir.glob('limbo_results_teastore_*.csv'):
                limbo_file = alt_file
                break

        if not limbo_file.exists():
            return pd.DataFrame()

        try:
            # Read CSV, skip first row if it contains metadata
            df = pd.read_csv(limbo_file)

            # Clean column names (remove spaces)
            df.columns = df.columns.str.strip()

            # Rename columns to standard format
            column_mapping = {
                'Target Time': 'target_time',
                'Load Intensity': 'load_intensity',
                'Successful Transactions': 'successful_transactions',
                'Failed Transactions': 'failed_transactions',
                'Dropped Transactions': 'dropped_transactions',
                'Avg Response Time': 'avg_response_time',
                'Final Batch Dispatch Time': 'final_batch_dispatch_time'
            }

            df = df.rename(columns=column_mapping)

            # Convert to numeric where needed
            numeric_cols = ['target_time', 'load_intensity', 'successful_transactions',
                          'failed_transactions', 'dropped_transactions', 'avg_response_time']

            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Calculate elapsed seconds from first target_time
            if not df.empty and 'target_time' in df.columns:
                min_time = df['target_time'].min()
                df['elapsed_seconds'] = df['target_time'] - min_time

            return df

        except Exception as e:
            print(f"Error loading limbo data from {limbo_file}: {e}")
            return pd.DataFrame()

    def load_informe_pids(self, experiment_path: str) -> pd.DataFrame:
        """
        Load informe_pids.csv file containing PID to process name mapping

        Args:
            experiment_path: Full path to experiment directory

        Returns:
            DataFrame with columns: node_name, pid, name_pid
        """
        exp_path = Path(experiment_path)
        pids_file = exp_path / 'informe_pids.csv'

        if not pids_file.exists():
            return pd.DataFrame(columns=['node_name', 'pid', 'name_pid'])

        try:
            df = pd.read_csv(pids_file)
            # Clean column names
            df.columns = df.columns.str.strip()

            # Handle column name variations
            if 'nodo_name' in df.columns:
                df = df.rename(columns={'nodo_name': 'node_name'})

            # Ensure required columns exist
            required_cols = ['node_name', 'pid', 'name_pid']
            for col in required_cols:
                if col not in df.columns:
                    print(f"Warning: {col} not found in informe_pids.csv")
                    return pd.DataFrame(columns=required_cols)

            # Convert pid to int
            df['pid'] = pd.to_numeric(df['pid'], errors='coerce')
            df = df.dropna(subset=['pid'])
            df['pid'] = df['pid'].astype(int)

            return df

        except Exception as e:
            print(f"Error loading informe_pids from {pids_file}: {e}")
            return pd.DataFrame(columns=['node_name', 'pid', 'name_pid'])

    def load_ecofloc_pid_data(self, experiment_path: str, component: str) -> pd.DataFrame:
        """
        Load per-PID Ecofloc energy data from raw files

        Args:
            experiment_path: Full path to experiment directory
            component: Component name (cpu, ram, nic, sd, unified)

        Returns:
            DataFrame with columns: node_name, pid, timestamp, energy_value
        """
        exp_path = Path(experiment_path)

        # Look in raw_results/ecofloc
        search_dir = exp_path / 'raw_results' / 'ecofloc'

        if not search_dir.exists():
            return pd.DataFrame(columns=['node_name', 'pid', 'timestamp', 'energy_value'])

        all_data = []

        # Find all ecofloc files
        for file_path in search_dir.glob('ecofloc_*.txt'):
            # Extract node name from filename: ecofloc_<node_name>_<component>.txt
            filename = file_path.name
            match = re.match(r'ecofloc_([^_]+)_(.+)\.txt', filename)
            if not match:
                continue

            node_name = match.group(1)
            file_component = match.group(2)

            # For unified, load all components; otherwise, match component
            if component != 'unified' and file_component != component:
                continue

            try:
                # Read the file, skip the first 2 lines (summary lines)
                with open(file_path, 'r') as f:
                    lines = f.readlines()

                # Skip header lines that start with "Average" or "Total"
                data_lines = [line for line in lines
                             if not line.startswith('Average')
                             and not line.startswith('Total')
                             and line.strip()]

                if not data_lines:
                    continue

                # Parse CSV data: timestamp,pid,value1,energy_value
                for line in data_lines:
                    parts = line.strip().split(',')
                    if len(parts) >= 4:
                        timestamp = parts[0]
                        pid = parts[1]
                        energy_value = float(parts[3])  # Column 4 (index 3)

                        all_data.append({
                            'node_name': node_name,
                            'pid': int(pid),
                            'timestamp': pd.to_datetime(timestamp),
                            'energy_value': energy_value
                        })

            except Exception as e:
                print(f"Error loading PID data from {file_path}: {e}")
                continue

        if not all_data:
            return pd.DataFrame(columns=['node_name', 'pid', 'timestamp', 'energy_value'])

        df = pd.DataFrame(all_data)
        df = df.sort_values(['node_name', 'pid', 'timestamp']).reset_index(drop=True)

        return df

    def load_ecofloc_component_data(self, experiment_path: str, target_component: str) -> pd.DataFrame:
        """
        Load Ecofloc data for a specific component only

        Args:
            experiment_path: Full path to experiment directory
            target_component: Specific component (cpu, ram, nic, sd)

        Returns:
            DataFrame with columns: node_name, timestamp, energy_value, elapsed_seconds
        """
        exp_path = Path(experiment_path)

        # Priority: clean_results first, then raw_results
        search_dirs = [
            exp_path / 'clean_results' / 'ecofloc',
            exp_path / 'raw_results' / 'ecofloc'
        ]

        all_data = []

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # Find all ecofloc files for this specific component
            for file_path in search_dir.glob(f'ecofloc_*_{target_component}.txt'):
                # Extract node name from filename: ecofloc_<node_name>_<component>.txt
                filename = file_path.name
                match = re.match(r'ecofloc_([^_]+)_(.+)\.txt', filename)
                if not match:
                    continue

                node_name = match.group(1)
                file_component = match.group(2)

                # Only load if component matches
                if file_component != target_component:
                    continue

                try:
                    # Read the file, skip the first 2 lines (summary lines)
                    with open(file_path, 'r') as f:
                        lines = f.readlines()

                    # Skip header lines that start with "Average" or "Total"
                    data_lines = [line for line in lines
                                 if not line.startswith('Average')
                                 and not line.startswith('Total')
                                 and line.strip()]

                    if not data_lines:
                        continue

                    # Parse CSV data: timestamp,value1,value2
                    rows = []
                    for line in data_lines:
                        parts = line.strip().split(',')
                        if len(parts) >= 3:
                            timestamp = parts[0]
                            energy_value = float(parts[2])  # Column 3 (index 2)
                            rows.append({
                                'node_name': node_name,
                                'timestamp': pd.to_datetime(timestamp),
                                'energy_value': energy_value
                            })

                    if rows:
                        all_data.extend(rows)

                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
                    continue

            # If we found data in clean_results, don't check raw_results
            if all_data:
                break

        if not all_data:
            return pd.DataFrame(columns=['node_name', 'timestamp', 'energy_value', 'elapsed_seconds'])

        df = pd.DataFrame(all_data)
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Calculate elapsed seconds from first timestamp
        if not df.empty and 'timestamp' in df.columns:
            min_timestamp = df['timestamp'].min()
            df['elapsed_seconds'] = (df['timestamp'] - min_timestamp).dt.total_seconds()

        return df
