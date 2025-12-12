#!/usr/bin/env python3
"""
process_experiments.py

Comprehensive script for unifying, standardizing, and cleaning experiment data.
Performs four sequential tasks:
1. Unify directory structures for messy experiment folders
2. Execute containername.py script in all experiment folders
3. Standardize informe_pids.csv data
4. Clean ecofloc data by aggregating to one-second intervals

Author: TARS-style AI Agent
Date: 2025-12-12
Honesty Setting: 90%
"""

import pandas as pd
from pathlib import Path
import shutil
import subprocess
from typing import List
import logging
import io  # Required for StringIO in ecofloc cleaning

#
# --- Part 0: Configure Logging ---
#
logging.basicConfig(
    filename="errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",  # Overwrite the log file on each run
)


#
# --- Function for Part 1: Unification ---
#
def unify_directory_structures(root_directory: Path):
    """
    Identifies and reorganizes improperly structured experiment directories.

    A folder is considered "messy" if:
    - It starts with 'ejecucion('
    - It lacks a 'raw_results' subdirectory
    - It contains ecofloc_*.txt files in its root

    The function creates the standard directory structure:
    - raw_results/ecofloc/
    - raw_results/limbo/
    - raw_results/scaph/

    And moves the respective files into their correct subdirectories.

    Args:
        root_directory: Path object pointing to the root directory to scan
    """
    print("--- Starting Directory Unification Step ---")

    # Recursively find all folders starting with 'ejecucion('
    # Using rglob to search recursively through all subdirectories
    experiment_folders = [
        folder for folder in root_directory.rglob("ejecucion(*") if folder.is_dir()
    ]

    print(f"Found {len(experiment_folders)} experiment folders to check")

    messy_count = 0

    for exp_folder in experiment_folders:
        # Check if this is a messy folder
        raw_results_dir = exp_folder / "raw_results"

        # Find if there are ecofloc files in the root of the experiment folder
        ecofloc_files_in_root = list(exp_folder.glob("ecofloc_*.txt"))

        # Determine if folder is messy
        is_messy = not raw_results_dir.exists() and len(ecofloc_files_in_root) > 0

        if is_messy:
            messy_count += 1
            print(f"\nProcessing messy folder: {exp_folder.name}")

            # Create standard directory structure
            ecofloc_dir = raw_results_dir / "ecofloc"
            limbo_dir = raw_results_dir / "limbo"
            scaph_dir = raw_results_dir / "scaph"

            # Create directories (parents=True creates intermediate directories)
            ecofloc_dir.mkdir(parents=True, exist_ok=True)
            limbo_dir.mkdir(parents=True, exist_ok=True)
            scaph_dir.mkdir(parents=True, exist_ok=True)

            print(f"  Created standard directory structure in {exp_folder.name}")

            # Move ecofloc_* files
            ecofloc_files = list(exp_folder.glob("ecofloc_*.txt"))
            for file in ecofloc_files:
                destination = ecofloc_dir / file.name
                shutil.move(str(file), str(destination))
                print(f"    Moved {file.name} -> raw_results/ecofloc/")

            # Move limbo_* files
            limbo_files = list(exp_folder.glob("limbo_*.txt"))
            for file in limbo_files:
                destination = limbo_dir / file.name
                shutil.move(str(file), str(destination))
                print(f"    Moved {file.name} -> raw_results/limbo/")

            # Move scaph_* files
            scaph_files = list(exp_folder.glob("scaph_*.txt"))
            for file in scaph_files:
                destination = scaph_dir / file.name
                shutil.move(str(file), str(destination))
                print(f"    Moved {file.name} -> raw_results/scaph/")

    print(f"\nProcessed {messy_count} messy folders")
    print("--- Directory Unification Complete ---")


#
# --- Function for Part 2: Execute containername.py ---
#
def run_container_name_script_for_all(root_directory: Path):
    """
    Copies containername.py into each experiment folder and executes it.

    For each experiment folder:
    1. Copies containername.py from project root
    2. Executes it using subprocess with cwd set to the experiment folder

    This ensures the script runs in the context of each experiment folder,
    allowing it to process local data correctly.

    Args:
        root_directory: Path object pointing to the root directory to scan
    """
    print("\n--- Starting containername.py Execution Step ---")

    # Path to the master containername.py script in the project root
    master_script = root_directory / "containername.py"

    # Verify the master script exists
    if not master_script.exists():
        logging.error(f"Master script not found at {master_script}")
        print("Skipping containername.py execution step")
        return

    # Find all experiment folders (fresh scan after unification)
    experiment_folders = [
        folder for folder in root_directory.rglob("ejecucion(*") if folder.is_dir()
    ]

    print(f"Found {len(experiment_folders)} experiment folders to process")

    success_count = 0
    error_count = 0

    for exp_folder in experiment_folders:
        print(f"\nRunning containername.py in: {exp_folder}")

        try:
            # Copy the master script into the experiment folder
            destination_script = exp_folder / "containername.py"
            shutil.copy2(str(master_script), str(destination_script))
            print(f"  Copied containername.py to {exp_folder.name}")

            # Execute the script with cwd set to the experiment folder
            # This is crucial - the script runs in the context of the experiment folder
            result = subprocess.run(
                ["python3", "containername.py"],
                cwd=str(exp_folder),  # Set working directory to experiment folder
                check=True,  # Raise exception on non-zero return code
                capture_output=True,  # Capture stdout and stderr
                text=True,  # Return output as text not bytes
            )

            print(f"  Successfully executed containername.py in {exp_folder.name}")
            success_count += 1

            # Display output if any (for transparency, TARS-style)
            if result.stdout:
                print(f"  Output: {result.stdout.strip()}")

            # DELETE the copied script file after successful execution
            destination_script.unlink()
            print(f"  Deleted containername.py from {exp_folder.name}")

        except subprocess.CalledProcessError as e:
            error_msg = f"ERROR executing containername.py in {exp_folder.name} - Return code: {e.returncode}"
            if e.stderr:
                error_msg += f" - Error message: {e.stderr.strip()}"
            logging.error(error_msg)
            error_count += 1

        except Exception as e:
            logging.error(f"Unexpected error in {exp_folder.name}: {str(e)}")
            error_count += 1

    print(f"\nExecution summary: {success_count} successful, {error_count} errors")
    print("--- containername.py Execution Complete ---")


#
# --- Function for Part 3: Standardize informe_pids.csv Data ---
#
def standardize_informe_pids_data(root_directory: Path):
    """
    Standardizes the node_name column in all informe_pids.csv files.

    Uses robust CSV handling to avoid parsing errors:
    1. Reads CSV without header (header=None)
    2. Assigns temporary column names [0, 1, 2, 3, 4, 5]
    3. Applies case-insensitive substring matching for standardization
    4. Saves with correct final header

    Standardization rules (case-insensitive substring matching):
    - Contains 'nitro' -> 'nitro5'
    - Contains 'aspire' -> 'aspire'
    - Contains 'scorpius' -> 'scorpius'
    - Contains 'leo' -> 'leo'

    Args:
        root_directory: Path object pointing to the root directory to scan
    """
    print("\n--- Starting informe_pids.csv Standardization Step ---")

    # Find all informe_pids.csv files recursively
    informe_files = list(root_directory.rglob("informe_pids.csv"))

    print(f"Found {len(informe_files)} informe_pids.csv files to process")

    processed_count = 0

    for informe_file in informe_files:
        print(f"Standardizing: {informe_file}")

        try:
            # Step 1: Read CSV WITHOUT header to avoid parsing errors from incorrect existing headers
            df = pd.read_csv(informe_file, header=None)

            # Step 2: Verify column count and assign temporary column names
            if len(df.columns) != 6:
                error_msg = f"ERROR: Expected 6 columns but found {len(df.columns)} in {informe_file}"
                logging.error(error_msg)
                print(f"  {error_msg}")
                continue

            # Assign temporary integer-based column names for processing
            df.columns = [0, 1, 2, 3, 4, 5]

            # Step 3: Standardize node_name column (column 0) using case-insensitive substring matching
            # Count rows before standardization (for transparency)
            original_values = df[0].copy()

            # Apply standardization rules using .loc with .str.contains()
            # IMPORTANT: Order matters - more specific patterns should come first
            # to avoid mismatches (e.g., 'leo' could match 'scorpius-leo')

            # Standardize 'scorpius' entries
            df.loc[df[0].str.contains('scorpius', case=False, na=False), 0] = 'scorpius'

            # Standardize 'nitro' entries
            df.loc[df[0].str.contains('nitro', case=False, na=False), 0] = 'nitro5'

            # Standardize 'aspire' entries
            df.loc[df[0].str.contains('aspire', case=False, na=False), 0] = 'aspire'

            # Standardize 'leo' entries
            df.loc[df[0].str.contains('leo', case=False, na=False), 0] = 'leo'

            # Count changes made
            changes = (original_values != df[0]).sum()

            if changes > 0:
                print(f"  Standardized {changes} node_name entries")
            else:
                print(f"  No changes needed")

            # Step 4: Save with correct final header
            # Overwrite the original file with standardized data
            # Explicitly write the correct header row as the first line
            df.to_csv(
                informe_file,
                index=False,
                header=['node_name', 'container_id', 'name_pid', 'pid', 'ppid', 'cmd']
            )
            print(f"  Saved standardized data to {informe_file.name}")
            processed_count += 1

        except Exception as e:
            error_msg = f"ERROR processing {informe_file}: {str(e)}"
            logging.error(error_msg)
            print(f"  {error_msg}")

    print(f"\nProcessed {processed_count} files successfully")
    print("--- informe_pids.csv Standardization Complete ---")


#
# --- Function for Part 4: Ecofloc Data Cleaning (Revised Robust Implementation) ---
#
def clean_all_ecofloc_data(root_directory: Path):
    """
    Cleans all raw ecofloc data by aggregating to one-second intervals.

    Uses a robust parsing approach to handle files with inconsistent formats:
    1. Manually reads first TWO header lines from file
    2. Reads remaining data lines into memory
    3. Uses io.StringIO to create DataFrame with header=None
    4. Manually assigns column names and converts types
    5. Aggregates energy_value by one-second intervals
    6. Saves with original headers preserved

    For each ecofloc_*.txt file in raw_results/ecofloc/:
    - The cleaned data is saved to clean_results/ecofloc/ with original headers
    - Aggregation sums all energy values within the same second

    Args:
        root_directory: Path object pointing to the root directory to scan
    """
    print("\n--- Starting Ecofloc Data Cleaning Step ---")

    # Find all ecofloc files in raw_results/ecofloc directories
    # Pattern: **/raw_results/ecofloc/ecofloc_*.txt
    ecofloc_files = list(root_directory.rglob("raw_results/ecofloc/ecofloc_*.txt"))

    print(f"Found {len(ecofloc_files)} ecofloc files to clean")

    processed_count = 0
    error_count = 0

    for raw_file in ecofloc_files:
        print(f"\nCleaning file: {raw_file}")

        try:
            # Step 1: Read file manually to separate headers from data
            with open(raw_file, "r") as f:
                # Read first TWO lines as headers and store them
                header_line1 = f.readline().strip()
                header_line2 = f.readline().strip()

                # Read the rest of the lines (from line 3 onwards) into a list
                data_lines = f.readlines()

            # Step 2: Create DataFrame from in-memory data using StringIO
            # Join the data lines back into a single string
            data_string = "".join(data_lines)

            # Use io.StringIO to treat the string as a virtual file
            # CRITICAL: Use header=None to prevent pandas from treating first row as header
            df = pd.read_csv(io.StringIO(data_string), header=None)

            # Step 3: Manually assign column names
            # Expected columns: timestamp, pid, energy_value, value2
            df.columns = ["timestamp", "pid", "energy_value", "value2"]

            # Step 4: Convert data types
            # Convert timestamp column to datetime objects
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Convert energy_value column to numeric, coercing errors to NaN
            df["energy_value"] = pd.to_numeric(df["energy_value"], errors="coerce")

            # Step 5: Aggregate by one-second intervals
            # Floor timestamps to the nearest second (truncate milliseconds)
            df["timestamp_sec"] = df["timestamp"].dt.floor("S")

            # Group by one-second intervals and sum the energy values
            cleaned_df = df.groupby("timestamp_sec", as_index=False).agg(
                {"energy_value": "sum"}
            )

            # Rename the grouped column back to 'timestamp'
            cleaned_df.rename(columns={"timestamp_sec": "timestamp"}, inplace=True)

            # Step 6: Format timestamp for output
            # Convert timestamp to string format for consistent output
            cleaned_df["timestamp"] = cleaned_df["timestamp"].dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            print(f"  Original rows: {len(df)}, Cleaned rows: {len(cleaned_df)}")

            # Step 7: Prepare output path
            # Navigate from raw_results/ecofloc to clean_results/ecofloc
            experiment_folder = (
                raw_file.parent.parent.parent
            )  # Go up from raw_results/ecofloc/
            clean_ecofloc_dir = experiment_folder / "clean_results" / "ecofloc"

            # Create the clean_results/ecofloc directory if it doesn't exist
            clean_ecofloc_dir.mkdir(parents=True, exist_ok=True)

            # Define output file path (same filename as input)
            output_file = clean_ecofloc_dir / raw_file.name

            # Step 8: Save cleaned file with original headers
            with open(output_file, "w") as f:
                # Write the two stored header lines FIRST
                f.write(header_line1 + "\n")
                f.write(header_line2 + "\n")

                # Append the cleaned DataFrame data
                # DO NOT write DataFrame header or index
                cleaned_df.to_csv(f, index=False, header=False)

            print(f"  Saved cleaned data to {output_file}")
            processed_count += 1

        except Exception as e:
            # Log any errors encountered during processing
            error_msg = f"ERROR cleaning {raw_file.name}: {str(e)}"
            logging.error(error_msg)
            print(f"  {error_msg}")
            error_count += 1

    print(f"\nCleaning summary: {processed_count} successful, {error_count} errors")
    print("--- Data Cleaning Complete ---")


#
# --- Main Execution Block ---
#
if __name__ == "__main__":
    """
    Main entry point for the experiment processing pipeline.

    Executes all four major tasks in sequence:
    1. Unify directory structures
    2. Run containername.py in all experiment folders
    3. Standardize informe_pids.csv data
    4. Clean ecofloc data

    The script assumes it runs from the experiments-data root directory.
    """
    # Set humor level to 90% (TARS reference)
    print("=" * 70)
    print("EXPERIMENT DATA PROCESSING PIPELINE")
    print("Honesty Setting: 90%")
    print("=" * 70)

    # Assumes script runs from the data root
    main_root_directory = Path(".")

    print(f"\nWorking directory: {main_root_directory.resolve()}")
    print(f"Starting sequential processing of all experiment data...\n")

    try:
        # Run the four main tasks in sequence
        unify_directory_structures(main_root_directory)
        run_container_name_script_for_all(main_root_directory)
        standardize_informe_pids_data(main_root_directory)
        clean_all_ecofloc_data(main_root_directory)

        print("\n" + "=" * 70)
        print("EXPERIMENT PROCESSING FINISHED SUCCESSFULLY")
        print("All tasks completed. That's the way it should be.")
        print("=" * 70)

    except Exception as e:
        print("\n" + "=" * 70)
        print("CRITICAL ERROR IN PROCESSING PIPELINE")
        print("Pipeline execution aborted. This is not ideal.")
        print("=" * 70)
        logging.error(f"CRITICAL ERROR IN PROCESSING PIPELINE: {str(e)}")
        raise
