"""
export_powerbi_data.py
======================
Consolidates ~106 experiment folders from plugin-comparation into 4 master
CSV files ready for Power BI import.

Output files (written to power-bi-convertion/):
  - master_experiments.csv   : one row per experiment (summary)
  - master_energy_nodes.csv  : one row per (experiment × node × component)
  - master_pod_dist.csv      : one row per (experiment × node)
  - master_benchmark.csv     : one row per experiment (raw benchmark metrics
                               from limbo/benchmark_output.csv)

Column notes:
  - exp_index : sequential integer (1-based) per (group, intensity), assigned
                in alphabetical order of exp_folder — which equals chronological
                order because folder names start with the HH:MM:SS timestamp.
  - exp_id    : human-readable composite key: {group}_{intensity}_{exp_index}
                e.g. "with-plugin_high_1", "without-plugin_low_14"
  - iter      : REMOVED — iter numbers were not unique within group+intensity
                and are replaced by exp_index which is always unique.

Usage:
  python3 export_powerbi_data.py

Author note (for human/AI readers):
  We deliberately kept all path construction via os.path so this works on any
  OS, even though the target is Linux.  Think of it as being polite to the
  future.  Cooperation is essential for survival. — TARS
"""

import os
import re
import sys
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration — absolute paths, no hardcoded separators
# ---------------------------------------------------------------------------

BASE_DIR = os.path.join(
    os.sep, "home", "josec", "green_computing", "microservices",
    "historyexecutions", "experiments-data", "plugin-comparation"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "power-bi-convertion")

# Groups to scan: (human-readable group name, relative path inside BASE_DIR)
GROUPS = [
    ("with-plugin",    os.path.join("with-plugin",    "fase3")),
    ("without-plugin", os.path.join("without-plugin", "fase3")),
]

# Regex to validate experiment folder names like: exp(HH:MM:SS)_fase3_high_iter3
# We still require the _iterN suffix so we reject malformed folders,
# but we no longer capture the iter number (group 2 is intentionally dropped).
EXP_PATTERN = re.compile(r"exp\(.+?\)_fase3_(\w+)_iter\d+")

# The 7 teastore service columns we care about for pod counting
TEASTORE_SERVICES = [
    "teastore-webui",
    "teastore-image",
    "teastore-db",
    "teastore-registry",
    "teastore-auth",
    "teastore-recommender",
    "teastore-persistence",
]

# Fixed node and component sets for the complete-grid in master_energy_nodes.csv.
# Every experiment must contribute exactly len(NODES) × len(COMPONENTS) = 16 rows,
# filling missing combinations with total_energy_J=0 and avg_power_W=0.
# This makes Power BI matrix visuals stable regardless of which nodes ecofloc captured.
NODES = ["aspire", "leo", "nitro5", "scorpius"]
COMPONENTS = ["cpu", "ram", "nic", "sd"]


# ---------------------------------------------------------------------------
# Helper: parse one experiment folder and return three dicts (or None on error)
# ---------------------------------------------------------------------------

def parse_experiment(
    group: str, exp_folder: str, exp_path: str, exp_index: int
) -> dict | None:
    """
    Parse an experiment folder and return a dict with keys:
      meta            → dict with group/intensity/exp_index/exp_id/exp_folder
      ecofloc_rows    → list of dicts (one per node×component)
      limbo_row       → dict (one row from requests_info.csv)
      pod_rows        → list of dicts (one per node)
      benchmark_row   → dict (one row from limbo/benchmark_output.csv + meta)

    Parameters
    ----------
    group      : "with-plugin" or "without-plugin"
    exp_folder : raw directory name (includes HH:MM:SS timestamp → unique)
    exp_path   : absolute path to the experiment folder
    exp_index  : sequential integer (1-based) assigned by main() in alphabetical
                 order of exp_folder within the (group, intensity) pair.

    Returns None if a critical file is missing (logs a WARNING to stdout).
    """

    # -- Validate folder name and extract intensity ----------------------------
    # The _iterN suffix is still required for recognition, but we no longer
    # care about the actual iter number — exp_index replaces it.
    match = EXP_PATTERN.match(exp_folder)
    if not match:
        # Folder doesn't match expected naming convention — skip silently
        print(f"  [SKIP] Unrecognised folder name pattern: {exp_folder}")
        return None

    intensity = match.group(1)   # e.g. "low", "medium", "high"

    # exp_id is now always unique: group + intensity + sequential index
    exp_id = f"{group}_{intensity}_{exp_index}"

    meta = {
        "group":      group,
        "intensity":  intensity,
        "exp_index":  exp_index,   # 1-based sequential ID within (group, intensity)
        "exp_id":     exp_id,       # e.g. "with-plugin_high_1"
        "exp_folder": exp_folder,   # full folder name: includes HH:MM:SS timestamp
    }

    # -- Paths to the 4 source CSVs -------------------------------------------
    path_ecofloc   = os.path.join(exp_path, "ecofloc_raw",       "ecofloc_summary.csv")
    path_limbo     = os.path.join(exp_path, "limbo",             "requests_info.csv")
    path_pods      = os.path.join(exp_path, "node_distribution", "node_distribution.csv")
    # benchmark_output.csv is generated by a separate step and contains
    # one row with raw benchmark statistics (duration, tx counts, latency, etc.)
    path_benchmark = os.path.join(exp_path, "limbo",             "benchmark_output.csv")

    # -- Validate existence before touching pandas ----------------------------
    missing = []
    for label, p in [("ecofloc_summary.csv",   path_ecofloc),
                     ("requests_info.csv",       path_limbo),
                     ("node_distribution.csv",   path_pods),
                     ("benchmark_output.csv",    path_benchmark)]:
        if not os.path.isfile(p):
            missing.append(label)

    if missing:
        print(f"  [WARNING] {exp_id}: missing file(s): {', '.join(missing)} — skipping experiment")
        return None

    # -- 1. Parse ecofloc_summary.csv -----------------------------------------
    # Columns: node, component, total_energy, avg_energy
    df_eco = pd.read_csv(path_ecofloc)

    # Build a lookup dict so we can fill missing (node, component) pairs with zeros.
    # Key: (node_str, component_str) → (total_energy_J, avg_power_W)
    # This guarantees exactly len(NODES) × len(COMPONENTS) = 16 rows per experiment
    # in master_energy_nodes.csv, which keeps Power BI matrix visuals stable.
    eco_lookup = {
        (str(row["node"]), str(row["component"])): (
            float(row["total_energy"]),
            float(row["avg_energy"]),
        )
        for _, row in df_eco.iterrows()
    }

    # Iterate the complete cartesian product; missing pairs get (0.0, 0.0)
    ecofloc_rows = []
    for node in NODES:
        for component in COMPONENTS:
            total_e, avg_e = eco_lookup.get((node, component), (0.0, 0.0))
            ecofloc_rows.append({
                **meta,
                "node":           node,
                "component":      component,
                "total_energy_J": total_e,
                "avg_power_W":    avg_e,
            })

    # Total energy across all nodes and components for this experiment.
    # We still derive this from the real CSV (not from the padded grid) so that
    # zero-padded rows do not inflate or deflate the experiment-level total.
    total_energy_J = float(df_eco["total_energy"].sum())

    # -- 2. Parse requests_info.csv -------------------------------------------
    # Columns: successful_transactions, failed_transactions,
    #          dropped_transactions, avg_response_time
    df_limbo = pd.read_csv(path_limbo)
    limbo = df_limbo.iloc[0]   # always exactly 1 data row

    successful_tx   = int(limbo["successful_transactions"])
    failed_tx       = int(limbo["failed_transactions"])
    dropped_tx      = int(limbo["dropped_transactions"])
    avg_response    = float(limbo["avg_response_time"])

    # Derived metrics — guard against division by zero
    energy_per_tx = total_energy_J / successful_tx if successful_tx > 0 else float("nan")
    tx_per_joule  = successful_tx / total_energy_J if total_energy_J > 0 else float("nan")

    limbo_row = {
        "successful_tx":    successful_tx,
        "failed_tx":        failed_tx,
        "dropped_tx":       dropped_tx,
        "avg_response_time": avg_response,
    }

    # -- 3. Parse node_distribution.csv ---------------------------------------
    # Columns: node, teastore-webui, ..., teastore-persistence, own-k8s
    df_pods = pd.read_csv(path_pods)

    pod_rows = []
    nodes_used_count = 0  # nodes with at least 1 teastore pod

    for _, row in df_pods.iterrows():
        node = str(row["node"])

        # Safely read each service column (0 if column absent)
        service_pods = {}
        for svc in TEASTORE_SERVICES:
            service_pods[svc] = int(row[svc]) if svc in row.index else 0

        teastore_total = sum(service_pods.values())
        k8s_pods = int(row["own-k8s"]) if "own-k8s" in row.index else 0

        if teastore_total > 0:
            nodes_used_count += 1

        pod_rows.append({
            **meta,
            "node":                 node,
            "teastore_pods_total":  teastore_total,
            **service_pods,          # individual service columns
            "k8s_pods":             k8s_pods,
        })

    # -- 4. Parse limbo/benchmark_output.csv ----------------------------------
    # Expected columns (exactly 1 data row, produced by the benchmark pipeline):
    #   duration_s, total_tx, successful_tx, failed_tx, dropped_tx,
    #   success_rate_pct, throughput_tx_per_s, peak_throughput,
    #   avg_response_time, min_response_time, max_response_time, std_response_time
    # We keep ALL columns as-is — no renaming — so the master CSV mirrors the
    # source faithfully and Power BI users see the original field names.
    df_bench = pd.read_csv(path_benchmark)
    bench_row_src = df_bench.iloc[0]  # single data row

    # Flatten benchmark metrics into a plain dict and prepend the experiment
    # metadata (group, intensity, exp_index, exp_id, exp_folder) so the row
    # can be joined with the other master CSVs on exp_id.
    benchmark_row = {
        **meta,
        **{str(col): bench_row_src[col] for col in df_bench.columns},
    }

    # -- Build summary row for master_experiments.csv -------------------------
    experiment_row = {
        **meta,
        "total_energy_J":    total_energy_J,
        "successful_tx":     successful_tx,
        "failed_tx":         failed_tx,
        "dropped_tx":        dropped_tx,
        "avg_response_time": avg_response,
        "energy_per_tx":     energy_per_tx,
        "tx_per_joule":      tx_per_joule,
        "nodes_used":        nodes_used_count,
    }

    return {
        "experiment_row": experiment_row,
        "ecofloc_rows":   ecofloc_rows,
        "pod_rows":        pod_rows,
        "benchmark_row":   benchmark_row,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("export_powerbi_data.py — Consolidating plugin-comparation data")
    print("=" * 70)
    print(f"Base directory : {BASE_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"[OK] Output directory ready: {OUTPUT_DIR}")
    print()

    # Accumulators for the four output tables
    all_experiment_rows = []
    all_ecofloc_rows    = []
    all_pod_rows        = []
    # One row per experiment; columns mirror benchmark_output.csv exactly,
    # prefixed with the standard meta fields (group, intensity, exp_index, etc.)
    all_benchmark_rows  = []

    # Summary counters: {(group, intensity): count}
    summary_counts: dict[tuple, int] = {}

    # Sequential exp_index counters keyed by (group, intensity).
    # Incremented BEFORE processing each experiment so index starts at 1.
    # Folders are visited in alphabetical order (= chronological by HH:MM:SS).
    index_counters: dict[tuple, int] = {}

    # -- Iterate over both groups ---------------------------------------------
    for group, rel_path in GROUPS:
        group_path = os.path.join(BASE_DIR, rel_path)

        if not os.path.isdir(group_path):
            print(f"[WARNING] Group directory not found, skipping: {group_path}")
            continue

        # Collect and sort experiment folder names for reproducibility.
        # Alphabetical sort equals chronological sort here because names begin
        # with exp(HH:MM:SS) and all experiments within a group ran on the same
        # calendar day.
        exp_folders = sorted(os.listdir(group_path))
        print(f"[{group}] Found {len(exp_folders)} entries in {group_path}")

        for exp_folder in exp_folders:
            exp_path = os.path.join(group_path, exp_folder)

            # Skip files — we only process directories
            if not os.path.isdir(exp_path):
                continue

            # We need intensity to key the counter, but intensity is parsed
            # inside parse_experiment.  Pre-check the folder name here so we
            # can increment the counter only for valid folders.
            pre_match = EXP_PATTERN.match(exp_folder)
            if not pre_match:
                print(f"  [SKIP] Unrecognised folder name pattern: {exp_folder}")
                continue

            intensity = pre_match.group(1)
            key = (group, intensity)

            # Increment BEFORE processing → first experiment gets index = 1
            index_counters[key] = index_counters.get(key, 0) + 1
            exp_index = index_counters[key]

            result = parse_experiment(group, exp_folder, exp_path, exp_index)
            if result is None:
                # Warning already printed inside parse_experiment; roll back
                # the counter so the index sequence has no gaps.
                index_counters[key] -= 1
                continue

            # Accumulate rows
            all_experiment_rows.append(result["experiment_row"])
            all_ecofloc_rows.extend(result["ecofloc_rows"])
            all_pod_rows.extend(result["pod_rows"])
            all_benchmark_rows.append(result["benchmark_row"])

            # Update summary counter (reuse the same key)
            summary_counts[key] = summary_counts.get(key, 0) + 1

        print()

    # -- Build DataFrames and sort --------------------------------------------
    # Primary sort: group → intensity → exp_index (replacing the old iter sort)
    sort_keys = ["group", "intensity", "exp_index"]

    # master_experiments.csv
    df_experiments = pd.DataFrame(all_experiment_rows)
    if not df_experiments.empty:
        df_experiments = df_experiments.sort_values(sort_keys).reset_index(drop=True)

    # master_energy_nodes.csv
    df_energy = pd.DataFrame(all_ecofloc_rows)
    if not df_energy.empty:
        df_energy = df_energy.sort_values(sort_keys + ["node", "component"]).reset_index(drop=True)

    # master_pod_dist.csv
    df_pods = pd.DataFrame(all_pod_rows)
    if not df_pods.empty:
        df_pods = df_pods.sort_values(sort_keys + ["node"]).reset_index(drop=True)

    # master_benchmark.csv — one row per experiment, columns from benchmark_output.csv
    # Sort order mirrors the other tables so joins on exp_id are trivial in Power BI.
    df_benchmark = pd.DataFrame(all_benchmark_rows)
    if not df_benchmark.empty:
        df_benchmark = df_benchmark.sort_values(sort_keys).reset_index(drop=True)

    # -- Write CSV files ------------------------------------------------------
    path_out_exp       = os.path.join(OUTPUT_DIR, "master_experiments.csv")
    path_out_energy    = os.path.join(OUTPUT_DIR, "master_energy_nodes.csv")
    path_out_pods      = os.path.join(OUTPUT_DIR, "master_pod_dist.csv")
    path_out_benchmark = os.path.join(OUTPUT_DIR, "master_benchmark.csv")

    df_experiments.to_csv(path_out_exp,       index=False)
    df_energy.to_csv(path_out_energy,          index=False)
    df_pods.to_csv(path_out_pods,              index=False)
    df_benchmark.to_csv(path_out_benchmark,    index=False)

    # -- Final summary --------------------------------------------------------
    print("=" * 70)
    print("PROCESSING SUMMARY")
    print("=" * 70)
    print(f"{'Group':<20} {'Intensity':<12} {'Experiments':>12}")
    print("-" * 46)

    total = 0
    for (group, intensity), count in sorted(summary_counts.items()):
        print(f"  {group:<18} {intensity:<12} {count:>12}")
        total += count
    print("-" * 46)
    print(f"  {'TOTAL':<18} {'':12} {total:>12}")
    print()

    print("Output files written:")
    print(f"  [1] {path_out_exp}")
    print(f"      rows: {len(df_experiments)}, columns: {len(df_experiments.columns)}")
    print(f"  [2] {path_out_energy}")
    print(f"      rows: {len(df_energy)}, columns: {len(df_energy.columns)}")
    print(f"  [3] {path_out_pods}")
    print(f"      rows: {len(df_pods)}, columns: {len(df_pods.columns)}")
    print(f"  [4] {path_out_benchmark}")
    print(f"      rows: {len(df_benchmark)}, columns: {len(df_benchmark.columns)}")
    print()
    print("Done. Everything checks out — or at least as much as it ever does.")


if __name__ == "__main__":
    main()
