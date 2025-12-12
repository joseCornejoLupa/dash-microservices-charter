"""
Test script to verify data loading functionality
"""

from data_loader import DataLoader
import pandas as pd

# Initialize data loader
ROOT_DIR = '/home/josec/green_computing/microservices/historyexecutions/experiments-data'
loader = DataLoader(ROOT_DIR)

print("=" * 80)
print("Testing Data Loader")
print("=" * 80)

# Test 1: Get available components
print("\n1. Available Components:")
components = loader.get_available_components()
print(f"   Found {len(components)} components: {components}")

# Test 2: Get intensities for CPU
if 'cpu' in components:
    print("\n2. Available Intensities for CPU:")
    intensities = loader.get_available_intensities('cpu')
    print(f"   Found {len(intensities)} intensities: {intensities}")

    # Test 3: Get experiments for CPU medium
    if 'med' in intensities:
        print("\n3. Available Experiments for CPU/Med:")
        experiments = loader.get_available_experiments('cpu', 'med')
        print(f"   Found {len(experiments)} experiments")
        if experiments:
            first_exp = experiments[0]
            print(f"   First experiment: {first_exp['label']}")

            # Test 4: Load Ecofloc data
            print("\n4. Testing Ecofloc Data Loading:")
            exp_path = first_exp['value']
            ecofloc_df = loader.load_ecofloc_data(exp_path, 'cpu')
            print(f"   Loaded {len(ecofloc_df)} rows")
            if not ecofloc_df.empty:
                print(f"   Columns: {list(ecofloc_df.columns)}")
                print(f"   Unique nodes: {ecofloc_df['node_name'].unique()}")
                print(f"   Sample data:")
                print(ecofloc_df.head(3))

            # Test 5: Load Scaphandre data
            print("\n5. Testing Scaphandre Data Loading:")
            scaph_df = loader.load_scaphandre_data(exp_path)
            print(f"   Loaded {len(scaph_df)} rows")
            if not scaph_df.empty:
                print(f"   Columns: {list(scaph_df.columns)}")
                print(f"   Unique nodes: {scaph_df['node_name'].unique()}")
                print(f"   Sample data:")
                print(scaph_df.head(3))

            # Test 6: Load Limbo data
            print("\n6. Testing Limbo Data Loading:")
            limbo_df = loader.load_limbo_data(exp_path, 'med')
            print(f"   Loaded {len(limbo_df)} rows")
            if not limbo_df.empty:
                print(f"   Columns: {list(limbo_df.columns)}")
                print(f"   Sample data:")
                print(limbo_df.head(3))

print("\n" + "=" * 80)
print("Testing Complete!")
print("=" * 80)
