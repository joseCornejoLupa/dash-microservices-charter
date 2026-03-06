"""
generate_benchmark_output.py
-----------------------------
For each experiment under with-plugin/fase3/ and without-plugin/fase3/,
reads all limbo_results_*.csv time-series files, computes a richer set of
benchmark metrics, and writes limbo/benchmark_output.csv (one data row).

This script extends the simpler requests_info.csv produced by
summarize_limbo_requests.py with additional statistics needed for
deeper analysis: throughput, peak throughput, response time distribution,
and success/drop rates.

Output columns (in order):
    duration_s, total_tx, successful_tx, failed_tx, dropped_tx,
    success_rate_pct, throughput_tx_per_s, peak_throughput,
    avg_response_time, min_response_time, max_response_time,
    std_response_time

Usage:
    /home/josec/green_computing/microservices/historyexecutions/
    experiments-data/new_data_set/venv/bin/python3 \
    /home/josec/.../plugin-comparation/python-files/generate_benchmark_output.py

Author: TARS (Claude Code)
"""

import glob
import os
import sys

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration — absolute paths, no relative nonsense
# ---------------------------------------------------------------------------

BASE_DIR = (
    "/home/josec/green_computing/microservices/historyexecutions/"
    "experiments-data/plugin-comparation"
)

# The two groups and the phase we care about
GROUPS_PHASE = [
    "with-plugin/fase3",
    "without-plugin/fase3",
]

OUTPUT_FILENAME = "benchmark_output.csv"

# Column names as they appear in the raw limbo CSV after index_col=0 parsing.
# The header row has 8 tokens (last token is a timestamp like
# '27.02.2026;00:03:19820'); data rows have only 7 values.
# Using index_col=0 promotes 'Target Time' to the row index, so the remaining
# 6 column headers align correctly with the 6 data columns.
COL_TARGET_TIME = "Target Time"   # This becomes the DataFrame index
COL_SUCCESSFUL  = "Successful Transactions"
COL_FAILED      = "Failed Transactions"
COL_DROPPED     = "Dropped Transactions"
COL_AVG_RT      = "Avg Response Time"

# Output column order — explicit, no surprises for downstream consumers
OUTPUT_COLUMNS = [
    "duration_s",
    "total_tx",
    "successful_tx",
    "failed_tx",
    "dropped_tx",
    "success_rate_pct",
    "throughput_tx_per_s",
    "peak_throughput",
    "avg_response_time",
    "min_response_time",
    "max_response_time",
    "std_response_time",
]


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------


def read_and_combine_csvs(csv_paths: list[str]) -> pd.DataFrame:
    """
    Reads one or more limbo_results_*.csv files and concatenates them
    into a single DataFrame.

    Limbo CSV quirk: the header line has 8 comma-separated tokens where the
    8th token is a wall-clock timestamp (e.g., '27.02.2026;00:03:19820').
    Data rows only have 7 values.  By passing index_col=0 pandas uses the
    first column (Target Time) as the row index, which shifts everything so
    the 6 remaining header names align with the 6 data columns.

    Args:
        csv_paths: list of absolute paths to limbo_results_*.csv files

    Returns:
        Combined DataFrame.  The index holds the Target Time float values.
        Empty DataFrame if all files were unreadable.
    """
    frames = []
    for path in sorted(csv_paths):
        try:
            df = pd.read_csv(path, index_col=0)
            frames.append(df)
        except Exception as exc:
            print(f"    WARNING: could not read {path} — {exc}")

    if not frames:
        return pd.DataFrame()

    # ignore_index=True resets the combined index so Target Time values from
    # different files don't collide (multi-file experiments restart at 0.5).
    return pd.concat(frames, ignore_index=False)


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------


def compute_benchmark_metrics(df: pd.DataFrame) -> dict:
    """
    Computes all benchmark metrics from the combined limbo DataFrame.

    Design decisions:
    - duration_s: the maximum Target Time across all combined rows.
      When multiple CSVs are combined (low+medium phases in the same run),
      the largest Target Time is the true experiment end.
    - Weighted avg_response_time: weight = Successful Transactions per row,
      restricted to rows where transactions > 0 to avoid dividing by zero
      and to exclude warm-up intervals with no traffic.
    - success_rate_pct: only counts attempted (successful + failed); dropped
      transactions are excluded from the denominator per limbo semantics
      (dropped = not dispatched, so they never reached the server).
    - std_response_time: population std of per-interval Avg Response Time
      (only active intervals).  Measures variability across time buckets,
      not per-request jitter.

    Args:
        df: Combined DataFrame with index=Target Time,
            columns including the COL_* constants above.

    Returns:
        dict with keys matching OUTPUT_COLUMNS.
    """
    # --- duration_s: highest Target Time value ---
    # The index holds Target Time floats after index_col=0 parsing.
    # We need to coerce to numeric in case pandas read them as object.
    target_times = pd.to_numeric(df.index, errors="coerce")
    duration_s = float(target_times.max()) if not target_times.empty else 0.0

    # --- transaction counts ---
    successful_tx = int(df[COL_SUCCESSFUL].sum())
    failed_tx     = int(df[COL_FAILED].sum())
    dropped_tx    = int(df[COL_DROPPED].sum())
    total_tx      = successful_tx + failed_tx + dropped_tx

    # --- success rate (success vs attempted; dropped excluded from denominator) ---
    attempted = successful_tx + failed_tx
    success_rate_pct = (successful_tx / attempted * 100.0) if attempted > 0 else 0.0

    # --- throughput (successful transactions per second of experiment) ---
    throughput_tx_per_s = (successful_tx / duration_s) if duration_s > 0 else 0.0

    # --- peak throughput (best single interval) ---
    peak_throughput = int(df[COL_SUCCESSFUL].max()) if not df.empty else 0

    # --- response time stats (only intervals with actual successful tx) ---
    active = df[df[COL_SUCCESSFUL] > 0]

    if active.empty:
        # Experiment produced zero successful transactions — all RT stats are undefined
        avg_response_time = 0.0
        min_response_time = 0.0
        max_response_time = 0.0
        std_response_time = 0.0
    else:
        weights = active[COL_SUCCESSFUL].astype(float)

        # Weighted average: each interval's RT contributes proportionally to
        # how many successful transactions it carried
        avg_response_time = float(
            (active[COL_AVG_RT] * weights).sum() / weights.sum()
        )

        # Simple min/max/std across active intervals (unweighted — reflects
        # the spread of experienced response times per second bucket)
        avg_rt_series = active[COL_AVG_RT].astype(float)
        min_response_time = float(avg_rt_series.min())
        max_response_time = float(avg_rt_series.max())
        std_response_time = float(avg_rt_series.std(ddof=1)) if len(avg_rt_series) > 1 else 0.0

    return {
        "duration_s":           round(duration_s, 3),
        "total_tx":             total_tx,
        "successful_tx":        successful_tx,
        "failed_tx":            failed_tx,
        "dropped_tx":           dropped_tx,
        "success_rate_pct":     round(success_rate_pct, 4),
        "throughput_tx_per_s":  round(throughput_tx_per_s, 6),
        "peak_throughput":      peak_throughput,
        "avg_response_time":    round(avg_response_time, 6),
        "min_response_time":    round(min_response_time, 6),
        "max_response_time":    round(max_response_time, 6),
        "std_response_time":    round(std_response_time, 6),
    }


# ---------------------------------------------------------------------------
# Per-experiment processing
# ---------------------------------------------------------------------------


def process_experiment(exp_dir: str) -> bool:
    """
    Processes a single experiment directory.

    Looks for limbo/limbo_results_*.csv, computes metrics, and writes
    limbo/benchmark_output.csv.  Always overwrites if output already exists.

    Args:
        exp_dir: absolute path to the experiment folder
                 (e.g., .../with-plugin/fase3/exp(00:06:18)_fase3_high_iter3)

    Returns:
        True if benchmark_output.csv was written, False if skipped.
    """
    exp_name = os.path.basename(exp_dir)
    limbo_dir = os.path.join(exp_dir, "limbo")

    # --- locate limbo_results_*.csv files ---
    csv_pattern = os.path.join(limbo_dir, "limbo_results_*.csv")
    csv_files   = glob.glob(csv_pattern)

    if not csv_files:
        print(f"  WARNING  {exp_name}  — no limbo_results_*.csv found, skipping")
        return False

    print(f"  PROC     {exp_name}  ({len(csv_files)} CSV file(s))")

    # --- read and combine all CSVs for this experiment ---
    combined_df = read_and_combine_csvs(csv_files)

    if combined_df.empty:
        print(f"    WARNING: combined DataFrame is empty — skipping output")
        return False

    # --- compute metrics ---
    metrics = compute_benchmark_metrics(combined_df)

    # --- write output ---
    output_path = os.path.join(limbo_dir, OUTPUT_FILENAME)
    row = pd.DataFrame([metrics])[OUTPUT_COLUMNS]   # enforce column order
    row.to_csv(output_path, index=False)

    # Brief summary line so the operator can eyeball the output instantly
    print(
        f"    -> {OUTPUT_FILENAME}  "
        f"duration={metrics['duration_s']}s  "
        f"successful_tx={metrics['successful_tx']}  "
        f"throughput={metrics['throughput_tx_per_s']:.2f}tx/s  "
        f"success_rate={metrics['success_rate_pct']:.1f}%  "
        f"avg_rt={metrics['avg_response_time']:.3f}s"
    )
    return True


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Iterates over all experiment directories under the two group/phase paths
    (with-plugin/fase3 and without-plugin/fase3) and generates
    benchmark_output.csv for each one.

    Counters are printed at the end so the operator knows what happened
    without having to parse every line of output.
    """
    print("=" * 70)
    print("generate_benchmark_output.py")
    print(f"Base directory: {BASE_DIR}")
    print("=" * 70)

    if not os.path.isdir(BASE_DIR):
        print(f"ERROR: base directory does not exist: {BASE_DIR}", file=sys.stderr)
        sys.exit(1)

    total_processed = 0
    total_skipped   = 0

    for group_phase in GROUPS_PHASE:
        phase_dir = os.path.join(BASE_DIR, group_phase)

        if not os.path.isdir(phase_dir):
            print(f"\nWARNING: directory not found, skipping: {phase_dir}")
            continue

        # Collect experiment sub-directories (alphabetical → deterministic order)
        exp_dirs = sorted([
            os.path.join(phase_dir, d)
            for d in os.listdir(phase_dir)
            if os.path.isdir(os.path.join(phase_dir, d))
        ])

        print(f"\nGroup: {group_phase}  ({len(exp_dirs)} experiment(s) found)")
        print("-" * 70)

        group_processed = 0
        group_skipped   = 0

        for exp_dir in exp_dirs:
            wrote = process_experiment(exp_dir)
            if wrote:
                group_processed += 1
            else:
                group_skipped += 1

        print(f"  Group summary — processed: {group_processed}  |  skipped: {group_skipped}")

        total_processed += group_processed
        total_skipped   += group_skipped

    # --- global summary ---
    print("\n" + "=" * 70)
    print(
        f"DONE.  "
        f"Total processed: {total_processed}  |  "
        f"Total skipped (WARNING): {total_skipped}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
