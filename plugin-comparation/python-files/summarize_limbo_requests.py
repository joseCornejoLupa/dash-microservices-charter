"""
summarize_limbo_requests.py
----------------------------
Processes all limbo/ subdirectories under plugin-comparation/ and generates
a requests_info.csv summary file in each one that contains limbo_results_*.csv data.

Directories belonging to fase1 and fase2 only have limbo_all.log (no CSV),
so those are automatically skipped when no matching CSV is found.

Output per processed limbo/ folder:
    requests_info.csv  — one data row with these columns:
        successful_transactions, failed_transactions, dropped_transactions, avg_response_time

avg_response_time is a weighted average using Successful Transactions as the
weight (only rows where Successful Transactions > 0 are included in the average).

Usage:
    python3 summarize_limbo_requests.py

Author: TARS (assisted by Claude Code)
"""

import glob
import os
import sys

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = "/home/josec/green_computing/microservices/historyexecutions/experiments-data/plugin-comparation"

# Column names as they appear after pandas reads the file with index_col=0.
# Because the header has 8 tokens and data rows have 7 values, pandas
# automatically promotes the first column (Target Time) to the index.
COL_SUCCESSFUL = "Successful Transactions"
COL_FAILED = "Failed Transactions"
COL_DROPPED = "Dropped Transactions"
COL_AVG_RT = "Avg Response Time"

OUTPUT_FILENAME = "requests_info.csv"


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def read_and_combine_csvs(csv_paths: list[str]) -> pd.DataFrame:
    """
    Reads one or more limbo_results_*.csv files and concatenates them
    into a single DataFrame.

    The CSV format quirk: the header row has 8 tokens (the last being a
    timestamp like '20.02.2026;10:20:53423'), while data rows only have 7
    values. Passing index_col=0 makes pandas use the first column
    (Target Time) as the row index, and the remaining 6 columns line up
    correctly with the 6 named column headers.
    """
    frames = []
    for path in sorted(csv_paths):
        try:
            df = pd.read_csv(path, index_col=0)
            frames.append(df)
        except Exception as exc:
            # If one file is malformed, report it and keep going
            print(f"    WARNING: could not read {path} — {exc}")
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def compute_summary(df: pd.DataFrame) -> dict:
    """
    Computes the four summary metrics from a combined DataFrame.

    Returns a dict ready to be written as a single-row CSV.
    """
    successful = int(df[COL_SUCCESSFUL].sum())
    failed = int(df[COL_FAILED].sum())
    dropped = int(df[COL_DROPPED].sum())

    # Weighted average response time: only rows with actual transactions
    active_rows = df[df[COL_SUCCESSFUL] > 0]
    if active_rows.empty:
        # No successful transactions at all — avg is meaningless, store 0.0
        avg_rt = 0.0
    else:
        weights = active_rows[COL_SUCCESSFUL]
        avg_rt = (active_rows[COL_AVG_RT] * weights).sum() / weights.sum()

    return {
        "successful_transactions": successful,
        "failed_transactions": failed,
        "dropped_transactions": dropped,
        "avg_response_time": round(avg_rt, 6),
    }


def write_summary(summary: dict, output_path: str) -> None:
    """Writes the summary dict as a single-row CSV to output_path."""
    row = pd.DataFrame([summary])
    # Enforce column order explicitly
    row = row[
        [
            "successful_transactions",
            "failed_transactions",
            "dropped_transactions",
            "avg_response_time",
        ]
    ]
    row.to_csv(output_path, index=False)


def process_limbo_dir(limbo_dir: str) -> bool:
    """
    Processes a single limbo/ directory.

    Returns True if a requests_info.csv was written, False if skipped.
    """
    # Find all CSV files matching the expected pattern
    csv_pattern = os.path.join(limbo_dir, "limbo_results_*.csv")
    csv_files = glob.glob(csv_pattern)

    if not csv_files:
        # Phase 1 and phase 2 directories fall here — expected, not an error
        print(f"  SKIP  {limbo_dir}  (no limbo_results_*.csv found)")
        return False

    print(f"  PROC  {limbo_dir}  ({len(csv_files)} CSV file(s))")

    # Read and combine all CSVs found in this limbo/ folder
    combined_df = read_and_combine_csvs(csv_files)
    if combined_df.empty:
        print(f"    WARNING: all CSVs were empty or unreadable — skipping output")
        return False

    # Compute the summary metrics
    summary = compute_summary(combined_df)

    # Write output — overwrite if already exists
    output_path = os.path.join(limbo_dir, OUTPUT_FILENAME)
    write_summary(summary, output_path)
    print(
        f"    -> {OUTPUT_FILENAME}  "
        f"successful={summary['successful_transactions']}  "
        f"failed={summary['failed_transactions']}  "
        f"dropped={summary['dropped_transactions']}  "
        f"avg_rt={summary['avg_response_time']}"
    )
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Walks the BASE_DIR tree recursively and processes every subdirectory
    named 'limbo/'.
    """
    print(f"Scanning base directory: {BASE_DIR}")
    print("-" * 70)

    if not os.path.isdir(BASE_DIR):
        print(f"ERROR: base directory does not exist: {BASE_DIR}", file=sys.stderr)
        sys.exit(1)

    # Collect all limbo/ directories via os.walk — deterministic alphabetical order
    limbo_dirs = []
    for root, dirs, _files in os.walk(BASE_DIR):
        # os.walk visits dirs alphabetically when sorted
        dirs.sort()
        for d in dirs:
            if d == "limbo":
                limbo_dirs.append(os.path.join(root, d))

    total = len(limbo_dirs)
    processed = 0
    skipped = 0

    for limbo_dir in limbo_dirs:
        wrote = process_limbo_dir(limbo_dir)
        if wrote:
            processed += 1
        else:
            skipped += 1

    print("-" * 70)
    print(
        f"Done.  Total limbo/ dirs found: {total}  |  "
        f"Processed: {processed}  |  Skipped: {skipped}"
    )


if __name__ == "__main__":
    main()
