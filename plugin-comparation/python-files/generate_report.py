"""
generate_report.py
==================
Generates a comparative analysis report between with-plugin and without-plugin
Kubernetes scheduling experiments (fase3).

EXECUTION ENVIRONMENT:
    This script requires matplotlib and numpy, available only in the new_data_set venv.
    Run it as follows:

        source /home/josec/green_computing/microservices/historyexecutions/ \
            experiments-data/new_data_set/venv/bin/activate
        python python-files/generate_report.py

OUTPUTS:
    - plugin-comparation/results/report.txt     (textual statistics + research answers)
    - plugin-comparation/results/graficos/*.png  (6 matplotlib figures)

AUTHOR: Claude Code (TARS-mode)
DATE:   2026-02-21
"""

# ── stdlib ──────────────────────────────────────────────────────────────────
import os
import re
import csv
import sys
import math
import warnings
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ── third-party (venv required) ─────────────────────────────────────────────
import matplotlib

matplotlib.use("Agg")  # headless: no GUI needed, writes PNGs directly
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

# Absolute base directory for plugin-comparation
BASE_DIR = Path(
    "/home/josec/green_computing/microservices/historyexecutions/"
    "experiments-data/plugin-comparation"
)

# The two experimental groups we iterate over
GROUPS = ["with-plugin", "without-plugin"]

# All teastore service columns in node_distribution.csv (excluding own-k8s)
TEASTORE_SERVICES = [
    "teastore-webui",
    "teastore-image",
    "teastore-db",
    "teastore-registry",
    "teastore-auth",
    "teastore-recommender",
    "teastore-persistence",
]

# Canonical node ordering for consistent plot axes
NODE_ORDER = ["aspire", "leo", "scorpius", "nitro5"]

# Color palette for the two groups (consistent across all plots)
GROUP_COLORS = {
    "with-plugin": "#4C72B0",  # muted blue
    "without-plugin": "#DD8452",  # muted orange
}

# Color palette for nodes (stacked bars + heatmap)
NODE_COLORS = {
    "aspire": "#2ecc71",
    "leo": "#3498db",
    "scorpius": "#e67e22",
    "nitro5": "#9b59b6",
}

# Intensity display order
INTENSITY_ORDER = ["low", "medium", "high"]


# ════════════════════════════════════════════════════════════════════════════
# DATA LOADING HELPERS
# ════════════════════════════════════════════════════════════════════════════


def parse_experiment_name(folder_name: str):
    """
    Extract (intensity, iteration) from folder names like:
        exp(10:24:17)_fase3_low_iter1
    Returns (intensity_str, iter_int) or (None, None) on failure.
    """
    pattern = r"exp\([\d:]+\)_fase3_(\w+)_iter(\d+)"
    match = re.search(pattern, folder_name)
    if match:
        return match.group(1).lower(), int(match.group(2))
    return None, None


def load_ecofloc_summary(exp_path: Path):
    """
    Read ecofloc_raw/ecofloc_summary.csv.

    Returns:
        total_energy_J  (float)   — sum of all total_energy values
        energy_by_node  (dict)    — {node: float} summed over components
    On missing file: returns (None, None) and prints a warning.
    """
    csv_path = exp_path / "ecofloc_raw" / "ecofloc_summary.csv"
    if not csv_path.exists():
        print(f"  [WARNING] Missing ecofloc_summary.csv in {exp_path.name}")
        return None, None

    total_energy = 0.0
    energy_by_node = defaultdict(float)

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Guard against blank trailing rows
            if not row.get("node") or not row.get("total_energy"):
                continue
            val = float(row["total_energy"])
            total_energy += val
            energy_by_node[row["node"].strip()] += val

    return total_energy, dict(energy_by_node)


def load_requests_info(exp_path: Path):
    """
    Read limbo/requests_info.csv.

    Returns dict with keys:
        successful_tx, failed_tx, dropped_tx, avg_response_time
    On missing file: returns None and prints a warning.
    """
    csv_path = exp_path / "limbo" / "requests_info.csv"
    if not csv_path.exists():
        print(f"  [WARNING] Missing requests_info.csv in {exp_path.name}")
        return None

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only one data row expected; return immediately
            return {
                "successful_tx": int(row["successful_transactions"]),
                "failed_tx": int(row["failed_transactions"]),
                "dropped_tx": int(row["dropped_transactions"]),
                "avg_response_time": float(row["avg_response_time"]),
            }
    # File existed but was empty / header-only
    print(f"  [WARNING] Empty requests_info.csv in {exp_path.name}")
    return None


def load_node_distribution(exp_path: Path):
    """
    Read node_distribution/node_distribution.csv.

    Returns:
        teastore_pods_per_node  (dict)  — {node: int} count of teastore pods
        raw_distribution        (dict)  — {node: {service: int}} full table
    On missing file: returns (None, None) and prints a warning.
    """
    csv_path = exp_path / "node_distribution" / "node_distribution.csv"
    if not csv_path.exists():
        print(f"  [WARNING] Missing node_distribution.csv in {exp_path.name}")
        return None, None

    teastore_pods_per_node = {}
    raw_distribution = {}

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            node = row.get("node", "").strip()
            if not node:
                continue
            svc_counts = {}
            teastore_total = 0
            for svc in TEASTORE_SERVICES:
                count = int(row.get(svc, 0))
                svc_counts[svc] = count
                teastore_total += count
            teastore_pods_per_node[node] = teastore_total
            raw_distribution[node] = svc_counts

    return teastore_pods_per_node, raw_distribution


# ════════════════════════════════════════════════════════════════════════════
# MAIN DATA COLLECTION
# ════════════════════════════════════════════════════════════════════════════


def collect_all_experiments():
    """
    Walk both groups / fase3 and build a list of per-experiment dicts.
    Each dict contains every metric needed for plots and the report.
    """
    records = []

    for group in GROUPS:
        fase3_dir = BASE_DIR / group / "fase3"
        if not fase3_dir.exists():
            print(
                f"[WARNING] fase3 directory not found for group '{group}': {fase3_dir}"
            )
            continue

        # Sort for deterministic ordering
        experiments = sorted(fase3_dir.iterdir())

        for exp_path in experiments:
            if not exp_path.is_dir():
                continue

            exp_name = exp_path.name
            intensity, iteration = parse_experiment_name(exp_name)

            if intensity is None:
                print(
                    f"  [WARNING] Could not parse experiment name: {exp_name}, skipping."
                )
                continue

            print(f"  Loading {group}/{exp_name} ...")

            # ── Load the three data sources ──────────────────────────────
            total_energy_J, energy_by_node = load_ecofloc_summary(exp_path)
            req_info = load_requests_info(exp_path)
            teastore_pods, raw_dist = load_node_distribution(exp_path)

            # ── Derived metrics ──────────────────────────────────────────
            successful_tx = req_info["successful_tx"] if req_info else None
            failed_tx = req_info["failed_tx"] if req_info else None
            dropped_tx = req_info["dropped_tx"] if req_info else None
            avg_response_time = req_info["avg_response_time"] if req_info else None

            # Energy efficiency: J per successful transaction
            if total_energy_J is not None and successful_tx and successful_tx > 0:
                energy_per_tx = total_energy_J / successful_tx
            else:
                energy_per_tx = None

            records.append(
                {
                    "group": group,
                    "intensity": intensity,
                    "iteration": iteration,
                    "experiment_name": exp_name,
                    "total_energy_J": total_energy_J,
                    "energy_by_node": energy_by_node,  # {node: float}
                    "successful_tx": successful_tx,
                    "failed_tx": failed_tx,
                    "dropped_tx": dropped_tx,
                    "avg_response_time": avg_response_time,
                    "energy_per_tx": energy_per_tx,
                    "teastore_pods_per_node": teastore_pods,  # {node: int}
                    "raw_distribution": raw_dist,  # {node: {svc: int}}
                }
            )

    return records


# ════════════════════════════════════════════════════════════════════════════
# STATISTICS HELPERS
# ════════════════════════════════════════════════════════════════════════════


def safe_mean(values):
    """Mean of a list, ignoring None entries. Returns None if list is empty."""
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else None


def safe_std(values):
    """Population std of a list, ignoring None. Returns None if < 2 elements."""
    clean = [v for v in values if v is not None]
    if len(clean) < 2:
        return 0.0
    mu = sum(clean) / len(clean)
    variance = sum((x - mu) ** 2 for x in clean) / len(clean)
    return math.sqrt(variance)


def group_records(records, group, intensity):
    """Filter records by (group, intensity) and return them."""
    return [r for r in records if r["group"] == group and r["intensity"] == intensity]


def aggregate_stats(recs, field):
    """Return (mean, std, values_list) for a scalar field across recs."""
    values = [r[field] for r in recs if r[field] is not None]
    return safe_mean(values), safe_std(values), values


def average_energy_by_node(recs):
    """
    Given a list of experiment records, compute average energy per node.
    Returns dict {node: avg_energy_float}.
    """
    accum = defaultdict(list)
    for r in recs:
        if r["energy_by_node"] is None:
            continue
        for node, energy in r["energy_by_node"].items():
            accum[node].append(energy)
    return {node: safe_mean(vals) for node, vals in accum.items()}


def average_pod_distribution(recs):
    """
    Compute average pod count per (node, service) across all records.
    Returns dict {node: {service: avg_float}}.
    """
    # Accumulate counts per (node, service)
    accum = defaultdict(lambda: defaultdict(list))
    for r in recs:
        if r["raw_distribution"] is None:
            continue
        for node, svc_counts in r["raw_distribution"].items():
            for svc, count in svc_counts.items():
                accum[node][svc].append(count)

    result = {}
    for node, svcs in accum.items():
        result[node] = {svc: safe_mean(counts) for svc, counts in svcs.items()}
    return result


def avg_teastore_nodes_used(recs):
    """
    Return average number of nodes that host at least one teastore pod,
    across all records in recs.
    """
    per_experiment = []
    for r in recs:
        if r["teastore_pods_per_node"] is None:
            continue
        nodes_used = sum(1 for v in r["teastore_pods_per_node"].values() if v > 0)
        per_experiment.append(nodes_used)
    return safe_mean(per_experiment)


# ════════════════════════════════════════════════════════════════════════════
# PLOT HELPERS
# ════════════════════════════════════════════════════════════════════════════


def _bar_x_positions(n_groups, n_intensities, bar_width=0.35):
    """
    Return x positions for grouped bar charts.
    n_groups:      number of group bars per intensity tick (2 typically)
    n_intensities: number of intensity categories
    Returns (x_base_array, offsets_list)
    """
    x = np.arange(n_intensities)
    # Offsets centered around 0 for n_groups bars
    half = (n_groups - 1) / 2.0
    offsets = [(i - half) * bar_width for i in range(n_groups)]
    return x, offsets, bar_width


def add_scatter_points(ax, x_center, values, color, marker="o", size=40, zorder=5):
    """
    Overlay individual experiment values as scatter dots over a bar.
    Adds a tiny horizontal jitter so overlapping points are visible.
    """
    n = len(values)
    if n == 0:
        return
    rng = np.random.default_rng(seed=42)  # deterministic jitter
    jitter = rng.uniform(-0.04, 0.04, size=n)
    for val, j in zip(values, jitter):
        if val is not None:
            ax.scatter(
                x_center + j,
                val,
                color=color,
                marker=marker,
                s=size,
                zorder=zorder,
                edgecolors="black",
                linewidths=0.5,
            )


# ════════════════════════════════════════════════════════════════════════════
# INDIVIDUAL PLOT FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════


def plot_energy_by_intensity(records, out_path: Path):
    """
    Grouped bar chart: avg total energy (J) per intensity × group.
    Individual experiment dots overlaid.
    """
    fig, ax = plt.subplots(figsize=(9, 5))
    bar_width = 0.35

    # Determine which intensities actually have data
    intensities_present = [
        i for i in INTENSITY_ORDER if any(r["intensity"] == i for r in records)
    ]
    x = np.arange(len(intensities_present))

    for gi, group in enumerate(GROUPS):
        offset = (gi - 0.5) * bar_width
        means, stds, all_vals_per_intensity = [], [], []

        for intensity in intensities_present:
            recs = group_records(records, group, intensity)
            m, s, vals = aggregate_stats(recs, "total_energy_J")
            means.append(m if m is not None else 0)
            stds.append(s if s is not None else 0)
            all_vals_per_intensity.append(vals)

        bars = ax.bar(
            x + offset,
            means,
            bar_width,
            label=group,
            color=GROUP_COLORS[group],
            alpha=0.85,
            yerr=stds,
            capsize=4,
            ecolor="grey",
        )

        # Scatter individual points
        for xi, vals in enumerate(all_vals_per_intensity):
            add_scatter_points(ax, x[xi] + offset, vals, color=GROUP_COLORS[group])

    ax.set_xticks(x)
    ax.set_xticklabels([i.capitalize() for i in intensities_present])
    ax.set_xlabel("Intensity")
    ax.set_ylabel("Total Energy (J)")
    ax.set_title("Average Total Energy by Intensity")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path.name}")


def plot_requests_by_intensity(records, out_path: Path):
    """
    Grouped bar chart: avg successful transactions per intensity × group.
    """
    fig, ax = plt.subplots(figsize=(9, 5))
    bar_width = 0.35

    intensities_present = [
        i for i in INTENSITY_ORDER if any(r["intensity"] == i for r in records)
    ]
    x = np.arange(len(intensities_present))

    for gi, group in enumerate(GROUPS):
        offset = (gi - 0.5) * bar_width
        means, stds, all_vals = [], [], []

        for intensity in intensities_present:
            recs = group_records(records, group, intensity)
            m, s, vals = aggregate_stats(recs, "successful_tx")
            means.append(m if m is not None else 0)
            stds.append(s if s is not None else 0)
            all_vals.append(vals)

        ax.bar(
            x + offset,
            means,
            bar_width,
            label=group,
            color=GROUP_COLORS[group],
            alpha=0.85,
            yerr=stds,
            capsize=4,
            ecolor="grey",
        )

        for xi, vals in enumerate(all_vals):
            add_scatter_points(ax, x[xi] + offset, vals, color=GROUP_COLORS[group])

    ax.set_xticks(x)
    ax.set_xticklabels([i.capitalize() for i in intensities_present])
    ax.set_xlabel("Intensity")
    ax.set_ylabel("Successful Transactions")
    ax.set_title("Average Successful Transactions by Intensity")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path.name}")


def plot_energy_efficiency(records, out_path: Path):
    """
    Grouped bar chart: avg energy per successful transaction (J/tx).
    """
    fig, ax = plt.subplots(figsize=(9, 5))
    bar_width = 0.35

    intensities_present = [
        i for i in INTENSITY_ORDER if any(r["intensity"] == i for r in records)
    ]
    x = np.arange(len(intensities_present))

    for gi, group in enumerate(GROUPS):
        offset = (gi - 0.5) * bar_width
        means, stds, all_vals = [], [], []

        for intensity in intensities_present:
            recs = group_records(records, group, intensity)
            m, s, vals = aggregate_stats(recs, "energy_per_tx")
            means.append(m if m is not None else 0)
            stds.append(s if s is not None else 0)
            all_vals.append(vals)

        ax.bar(
            x + offset,
            means,
            bar_width,
            label=group,
            color=GROUP_COLORS[group],
            alpha=0.85,
            yerr=stds,
            capsize=4,
            ecolor="grey",
        )

        for xi, vals in enumerate(all_vals):
            add_scatter_points(ax, x[xi] + offset, vals, color=GROUP_COLORS[group])

    ax.set_xticks(x)
    ax.set_xticklabels([i.capitalize() for i in intensities_present])
    ax.set_xlabel("Intensity")
    ax.set_ylabel("J / successful transaction")
    ax.set_title("Energy per Successful Transaction (Efficiency)")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path.name}")


def plot_failed_tx(records, out_path: Path):
    """
    Grouped bar chart: avg failed transactions per intensity × group.
    """
    fig, ax = plt.subplots(figsize=(9, 5))
    bar_width = 0.35

    intensities_present = [
        i for i in INTENSITY_ORDER if any(r["intensity"] == i for r in records)
    ]
    x = np.arange(len(intensities_present))

    for gi, group in enumerate(GROUPS):
        offset = (gi - 0.5) * bar_width
        means, stds, all_vals = [], [], []

        for intensity in intensities_present:
            recs = group_records(records, group, intensity)
            m, s, vals = aggregate_stats(recs, "failed_tx")
            means.append(m if m is not None else 0)
            stds.append(s if s is not None else 0)
            all_vals.append(vals)

        ax.bar(
            x + offset,
            means,
            bar_width,
            label=group,
            color=GROUP_COLORS[group],
            alpha=0.85,
            yerr=stds,
            capsize=4,
            ecolor="grey",
        )

        for xi, vals in enumerate(all_vals):
            add_scatter_points(ax, x[xi] + offset, vals, color=GROUP_COLORS[group])

    ax.set_xticks(x)
    ax.set_xticklabels([i.capitalize() for i in intensities_present])
    ax.set_xlabel("Intensity")
    ax.set_ylabel("Failed Transactions")
    ax.set_title("Average Failed Transactions by Intensity")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path.name}")


def plot_node_energy_breakdown(records, out_path: Path):
    """
    Stacked bar chart showing average energy contribution per node,
    one subplot per intensity (low, medium, high), showing with-plugin vs
    without-plugin side-by-side within each subplot.

    Only intensities that have data in BOTH groups are rendered, so the
    figure degrades gracefully when new experiments are added over time.
    """
    # Determine which intensities have data for BOTH groups simultaneously
    intensities_with_both = [
        intensity
        for intensity in INTENSITY_ORDER
        if group_records(records, "with-plugin", intensity)
        and group_records(records, "without-plugin", intensity)
    ]

    if not intensities_with_both:
        print(
            "  [WARNING] No intensity has data in both groups — skipping node breakdown."
        )
        return

    n_subplots = len(intensities_with_both)
    # Each subplot is ~5 inches wide; legend sits outside the last panel
    fig, axes = plt.subplots(
        1, n_subplots, figsize=(5 * n_subplots + 1.5, 5), sharey=False
    )

    # Make axes always iterable (when n_subplots == 1, plt returns a single Axes)
    if n_subplots == 1:
        axes = [axes]

    for ax, intensity in zip(axes, intensities_with_both):
        labels = []
        # Accumulate per-node energy values per group bar
        bottom_vals = {node: [] for node in NODE_ORDER}

        for group in GROUPS:
            recs = group_records(records, group, intensity)
            if not recs:
                continue
            avg_by_node = average_energy_by_node(recs)
            labels.append(group)
            for node in NODE_ORDER:
                bottom_vals[node].append(avg_by_node.get(node, 0.0) or 0.0)

        x = np.arange(len(labels))
        bottoms = np.zeros(len(labels))

        for node in NODE_ORDER:
            vals = bottom_vals[node]
            ax.bar(
                x, vals, bottom=bottoms, label=node, color=NODE_COLORS[node], alpha=0.9
            )
            bottoms += np.array(vals)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylabel("Average Total Energy (J)")
        ax.set_title(f"{intensity.capitalize()} Intensity", fontsize=11)
        ax.grid(axis="y", linestyle="--", alpha=0.4)

    # Draw a shared legend only once, taken from the last subplot
    handles, leg_labels = axes[-1].get_legend_handles_labels()
    fig.legend(
        handles, leg_labels, title="Node", bbox_to_anchor=(1.0, 0.9), loc="upper left"
    )

    fig.suptitle("Energy Breakdown by Node — by Intensity", fontsize=13)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path.name}")


def plot_pod_distribution_heatmap(records, out_path: Path):
    """
    Grid of heatmaps showing average pod distribution per (node x service),
    broken down by intensity AND group.

    Layout:
        - One ROW per intensity (low, medium, high) — only rendered when BOTH
          groups have data for that intensity.
        - Two COLUMNS per row: with-plugin (left) | without-plugin (right).

    Each cell colour encodes the average number of pods of a given service
    that ran on that node across all iterations of that (group, intensity) combo.

    Axes:
        - Rows (y-axis): nodes in NODE_ORDER
        - Columns (x-axis): teastore services in TEASTORE_SERVICES (shortened)

    The colour scale (YlOrRd) is computed independently per subplot so that
    low-count intensities are still visually informative.

    A shared figure title and per-subplot subtitle convey group and intensity.
    The plot is saved to out_path; the caller is unchanged.
    """
    # Determine which intensities have data in BOTH groups simultaneously
    intensities_with_both = [
        intensity
        for intensity in INTENSITY_ORDER
        if group_records(records, "with-plugin", intensity)
        and group_records(records, "without-plugin", intensity)
    ]

    if not intensities_with_both:
        print(
            "  [WARNING] No intensity has data in both groups"
            " — skipping pod distribution heatmap."
        )
        return

    n_rows = len(intensities_with_both)   # one row per intensity
    n_cols = 2                             # always: with-plugin | without-plugin

    # Each heatmap cell is ~2 inches wide × ~1.5 inches per node tall;
    # add generous padding for labels and colorbars.
    cell_w = 2.2 * len(TEASTORE_SERVICES)  # ~15 inches for 7 services
    cell_h = 1.4 * len(NODE_ORDER)         # ~5.6 inches for 4 nodes
    fig, axes = plt.subplots(
        n_rows, n_cols,
        figsize=(cell_w, cell_h * n_rows + 1.0),
        squeeze=False,  # always return 2-D array of axes
    )

    fig.suptitle(
        "Average Pod Distribution per Node — by Intensity",
        fontsize=14,
        y=1.01,
    )

    # Shortened service names for readability on x-axis ticks
    svc_labels = [s.replace("teastore-", "") for s in TEASTORE_SERVICES]

    for row_idx, intensity in enumerate(intensities_with_both):
        for col_idx, group in enumerate(GROUPS):
            ax = axes[row_idx][col_idx]

            # Fetch records for this (group, intensity) cell
            recs = group_records(records, group, intensity)
            avg_dist = average_pod_distribution(recs)

            # Build the numeric matrix: rows=nodes, cols=services
            matrix = np.zeros((len(NODE_ORDER), len(TEASTORE_SERVICES)))
            for ri, node in enumerate(NODE_ORDER):
                if node in avg_dist:
                    for ci, svc in enumerate(TEASTORE_SERVICES):
                        matrix[ri, ci] = avg_dist[node].get(svc, 0.0)

            # vmax per subplot — floor at 1 so a zero-only matrix is not degenerate
            vmax = max(1.0, float(matrix.max()))

            im = ax.imshow(
                matrix,
                cmap="YlOrRd",
                aspect="auto",
                vmin=0,
                vmax=vmax,
            )

            # Axis ticks and labels
            ax.set_xticks(range(len(TEASTORE_SERVICES)))
            ax.set_xticklabels(svc_labels, rotation=35, ha="right", fontsize=8)
            ax.set_yticks(range(len(NODE_ORDER)))
            ax.set_yticklabels(NODE_ORDER, fontsize=9)

            # Subplot title encodes both dimensions for clarity
            ax.set_title(
                f"{group} — {intensity.capitalize()}",
                fontsize=10,
                pad=6,
            )

            # Annotate each cell with its numeric average value
            for ri in range(len(NODE_ORDER)):
                for ci in range(len(TEASTORE_SERVICES)):
                    val = matrix[ri, ci]
                    # Switch to white text on dark backgrounds for readability
                    text_color = "white" if val > vmax * 0.6 else "black"
                    ax.text(
                        ci,
                        ri,
                        f"{val:.2f}",
                        ha="center",
                        va="center",
                        fontsize=7,
                        color=text_color,
                    )

            # Individual colorbar for each subplot
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Avg pods")

    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path.name}")


# ════════════════════════════════════════════════════════════════════════════
# REPORT TEXT GENERATION
# ════════════════════════════════════════════════════════════════════════════


def _pct_diff(a, b):
    """
    Percentage difference of a relative to b.
    Positive = a is larger, negative = a is smaller.
    Returns (float_pct, 'more'/'less') or (None, '') if inputs invalid.
    """
    if a is None or b is None or b == 0:
        return None, ""
    pct = ((a - b) / b) * 100
    direction = "more" if pct >= 0 else "less"
    return abs(pct), direction


def build_stat_table(records):
    """
    Build a formatted ASCII table with one row per (group × intensity).
    Returns list of strings (lines).
    """
    header = (
        f"{'Group':<18} {'Intensity':<10} {'N':>3}  "
        f"{'avg_energy_J':>13} {'std_energy':>11}  "
        f"{'avg_succ_tx':>11} {'std_tx':>8}  "
        f"{'avg_J/tx':>9}"
    )
    sep = "-" * len(header)
    rows = [header, sep]

    for group in GROUPS:
        for intensity in INTENSITY_ORDER:
            recs = group_records(records, group, intensity)
            if not recs:
                continue
            n = len(recs)
            me, se, _ = aggregate_stats(recs, "total_energy_J")
            mt, st, _ = aggregate_stats(recs, "successful_tx")
            mj, sj, _ = aggregate_stats(recs, "energy_per_tx")

            def _fmt(v, decimals=2):
                return f"{v:.{decimals}f}" if v is not None else "N/A"

            rows.append(
                f"{group:<18} {intensity:<10} {n:>3}  "
                f"{_fmt(me):>13} {_fmt(se):>11}  "
                f"{_fmt(mt, 1):>11} {_fmt(st, 1):>8}  "
                f"{_fmt(mj, 4):>9}"
            )

    return rows


def generate_report_text(records):
    """
    Compose the full report as a multiline string.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sep_major = "=" * 60
    sep_minor = "-" * 60

    lines = []
    lines.append(sep_major)
    lines.append("PLUGIN SCHEDULING COMPARISON REPORT")
    lines.append(f"Generated: {now_str}")
    lines.append(sep_major)
    lines.append("")

    # ── DATASET SUMMARY ──────────────────────────────────────────────────
    lines.append("DATASET SUMMARY")
    lines.append(sep_minor)

    for group in GROUPS:
        grp_recs = [r for r in records if r["group"] == group]
        n_total = len(grp_recs)
        intensity_counts = defaultdict(int)
        for r in grp_recs:
            intensity_counts[r["intensity"]] += 1
        detail = ", ".join(f"{k}={v}" for k, v in sorted(intensity_counts.items()))
        intensities_str = ", ".join(sorted(intensity_counts.keys()))
        lines.append(
            f"- Experiments {group:<18}: {n_total:>2}"
            f"  ({intensities_str})"
            f"  [{detail}]"
        )

    lines.append("")

    # ── RAW STATISTICS TABLE ─────────────────────────────────────────────
    lines.append("RAW STATISTICS (grouped by plugin x intensity)")
    lines.append(sep_minor)
    lines.extend(build_stat_table(records))
    lines.append("")

    # Helper: format a float value with d decimal places, or "N/A"
    def _fv(v, d=2):
        return f"{v:.{d}f}" if v is not None else "N/A"

    # Pre-compute per-(group, intensity) stats once; reused by RQ1, RQ2, RQ3
    # Structure: stats[group][intensity] = {field: (mean, std, values)}
    stats = {}
    for g in GROUPS:
        stats[g] = {}
        for intensity in INTENSITY_ORDER:
            recs_gi = group_records(records, g, intensity)
            n = len(recs_gi)
            if n == 0:
                stats[g][intensity] = None
                continue
            me, se, ve = aggregate_stats(recs_gi, "total_energy_J")
            mt, st, vt = aggregate_stats(recs_gi, "successful_tx")
            mj, sj, vj = aggregate_stats(recs_gi, "energy_per_tx")
            stats[g][intensity] = {
                "n": n,
                "energy": (me, se),
                "tx": (mt, st),
                "j_per_tx": (mj, sj),
            }

    # ── RQ1: Energy ──────────────────────────────────────────────────────
    lines.append("RESEARCH QUESTION 1: Does the plugin reduce energy consumption?")
    lines.append(sep_minor)
    lines.append("Comparison by intensity (with-plugin vs without-plugin):")
    lines.append("")

    # Track how many intensities show the plugin using less energy
    rq1_less_count = 0
    rq1_compared = 0

    for intensity in INTENSITY_ORDER:
        wp_stat = stats["with-plugin"][intensity]
        wop_stat = stats["without-plugin"][intensity]

        # Skip intensities missing from either group
        if wp_stat is None or wop_stat is None:
            continue

        n_wp = wp_stat["n"]
        n_wop = wop_stat["n"]
        wp_e_mean, wp_e_std = wp_stat["energy"]
        wop_e_mean, wop_e_std = wop_stat["energy"]

        lines.append(f"  {intensity.upper()} intensity (N_wp={n_wp} vs N_wop={n_wop}):")
        lines.append(
            f"    with-plugin    avg: {_fv(wp_e_mean)} J  (std: {_fv(wp_e_std)})"
        )
        lines.append(
            f"    without-plugin avg: {_fv(wop_e_mean)} J  (std: {_fv(wop_e_std)})"
        )

        pct, direction = _pct_diff(wp_e_mean, wop_e_mean)
        if pct is not None:
            lines.append(
                f"    Difference: {pct:.1f}% {direction} energy with the plugin"
            )
            rq1_compared += 1
            if direction == "less":
                rq1_less_count += 1
        else:
            lines.append("    Difference: insufficient data to compare.")
        lines.append("")

    # Dynamic overall interpretation based on how many intensities favour plugin
    if rq1_compared > 0:
        if rq1_less_count >= 2:
            rq1_overall = (
                "The plugin consistently uses LESS energy across intensities,"
                " confirming the consolidation hypothesis."
            )
        elif rq1_less_count == 0:
            rq1_overall = (
                "The plugin consistently uses MORE energy across intensities."
                " Investigate scheduling overhead or workload mismatch."
            )
        else:
            rq1_overall = "Results are mixed across intensities."
    else:
        rq1_overall = "Insufficient data for an overall interpretation."

    lines.append(f"  Overall interpretation: {rq1_overall}")
    lines.append("  See: energy_by_intensity.png, node_energy_breakdown.png")
    lines.append("")

    # ── RQ2: Transactions ─────────────────────────────────────────────────
    lines.append(
        "RESEARCH QUESTION 2: Does the plugin improve successful request rate?"
    )
    lines.append(sep_minor)
    lines.append("Comparison by intensity:")
    lines.append("")

    rq2_more_count = 0
    rq2_compared = 0

    for intensity in INTENSITY_ORDER:
        wp_stat = stats["with-plugin"][intensity]
        wop_stat = stats["without-plugin"][intensity]

        if wp_stat is None or wop_stat is None:
            continue

        n_wp = wp_stat["n"]
        n_wop = wop_stat["n"]
        wp_t_mean, wp_t_std = wp_stat["tx"]
        wop_t_mean, wop_t_std = wop_stat["tx"]

        lines.append(f"  {intensity.upper()} intensity (N_wp={n_wp} vs N_wop={n_wop}):")
        lines.append(
            f"    with-plugin    avg: {_fv(wp_t_mean, 1)} tx  (std: {_fv(wp_t_std, 1)})"
        )
        lines.append(
            f"    without-plugin avg: {_fv(wop_t_mean, 1)} tx  (std: {_fv(wop_t_std, 1)})"
        )

        pct2, direction2 = _pct_diff(wp_t_mean, wop_t_mean)
        if pct2 is not None:
            lines.append(
                f"    Difference: {pct2:.1f}% {direction2} successful tx with the plugin"
            )
            rq2_compared += 1
            if direction2 == "more":
                rq2_more_count += 1
        else:
            lines.append("    Difference: insufficient data to compare.")

        # High-variance note applies only to without-plugin low intensity
        if intensity == "low":
            lines.append(
                "    NOTE: without-plugin low has high variance"
                " (two distinct batches: ~1500 tx vs ~4800 tx)"
            )
        lines.append("")

    if rq2_compared > 0:
        if rq2_more_count >= 2:
            rq2_overall = (
                "The plugin consistently achieves MORE successful transactions,"
                " suggesting better resource allocation across load levels."
            )
        elif rq2_more_count == 0:
            rq2_overall = (
                "The plugin consistently achieves FEWER successful transactions."
                " Could indicate scheduling overhead or specific workload mismatch."
            )
        else:
            rq2_overall = "Results are mixed across intensities."
    else:
        rq2_overall = "Insufficient data for an overall interpretation."

    lines.append(f"  Overall interpretation: {rq2_overall}")
    lines.append("  See: requests_by_intensity.png")
    lines.append("")

    # ── RQ3: Efficiency + Pod distribution ───────────────────────────────
    lines.append(
        "RESEARCH QUESTION 3: Combined efficiency and pod-distribution impact?"
    )
    lines.append(sep_minor)
    lines.append("Energy efficiency (J per successful transaction) by intensity:")
    lines.append("")

    for intensity in INTENSITY_ORDER:
        wp_stat = stats["with-plugin"][intensity]
        wop_stat = stats["without-plugin"][intensity]

        if wp_stat is None or wop_stat is None:
            continue

        wp_j_mean, _ = wp_stat["j_per_tx"]
        wop_j_mean, __ = wop_stat["j_per_tx"]

        pct3, direction3 = _pct_diff(wp_j_mean, wop_j_mean)
        if pct3 is not None:
            verdict = "better" if direction3 == "less" else "worse"
            diff_str = f"{pct3:.1f}% {verdict}"
        else:
            diff_str = "N/A"

        lines.append(
            f"  {intensity.upper():6s}: "
            f"with-plugin {_fv(wp_j_mean, 4)} J/tx  vs  "
            f"without-plugin {_fv(wop_j_mean, 4)} J/tx  "
            f"→ {diff_str}"
        )

    lines.append("")
    lines.append("Pod distribution mechanism (avg nodes hosting at least one teastore pod)")
    lines.append("")

    # Count how many intensities show with-plugin using fewer nodes than without-plugin.
    # We iterate over ALL intensities so the reader can see the full picture.
    consolidation_count = 0   # intensities where with-plugin < without-plugin nodes
    compared_count = 0        # intensities with valid data in both groups

    for intensity in INTENSITY_ORDER:
        wp_recs = group_records(records, "with-plugin", intensity)
        wop_recs = group_records(records, "without-plugin", intensity)

        # Skip if either group has no data for this intensity
        if not wp_recs or not wop_recs:
            continue

        wp_nodes = avg_teastore_nodes_used(wp_recs)
        wop_nodes = avg_teastore_nodes_used(wop_recs)

        # Format the line: label padded for alignment
        label = f"  {intensity.upper():6s}:"
        wp_str = f"with-plugin {_fv(wp_nodes, 2)} node(s)"
        wop_str = f"without-plugin {_fv(wop_nodes, 2)} node(s)"
        lines.append(f"{label}  {wp_str}  |  {wop_str}")

        # Accumulate direction counts for the overall implication
        if wp_nodes is not None and wop_nodes is not None:
            compared_count += 1
            if wp_nodes < wop_nodes:
                consolidation_count += 1

    lines.append("")

    # Derive the overall implication from how often the plugin consolidates
    if compared_count == 0:
        implication = "Insufficient pod-distribution data to draw a conclusion."
    elif consolidation_count == compared_count:
        implication = (
            f"Across all {compared_count} compared intensities the plugin consistently"
            " consolidates workloads onto fewer nodes, potentially reducing inter-node"
            " network traffic and enabling deeper sleep states on idle nodes."
        )
    elif consolidation_count == 0:
        implication = (
            f"Across all {compared_count} compared intensities the plugin consistently"
            " spreads workloads over MORE nodes than the default scheduler,"
            " which may reduce per-node hotspots but prevents idle-node sleep states."
        )
    else:
        implication = (
            f"The plugin consolidates onto fewer nodes in {consolidation_count}"
            f" of {compared_count} intensities. Behaviour is mixed — inspect"
            " the pod_distribution_heatmap for a per-intensity view."
        )

    lines.append(f"  Implication: {implication}")

    lines.append("  See: energy_efficiency.png, pod_distribution_heatmap.png")
    lines.append("")

    # ── LIMITATIONS ───────────────────────────────────────────────────────
    lines.append("LIMITATIONS")
    lines.append(sep_minor)
    lines.append(
        "- without-plugin low intensity has high variance due to"
        " two distinct experimental batches."
    )
    lines.append(
        "- ecofloc measures total node energy;"
        " it cannot isolate individual pod consumption."
    )
    lines.append(
        "- with-plugin has fewer replications per intensity (2) vs without-plugin (3-7);"
        " interpret std with caution."
    )
    lines.append("- pod_distribution_heatmap.")
    lines.append("")
    lines.append(sep_major)

    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════


def main():
    print("\n" + "=" * 60)
    print("PLUGIN COMPARISON REPORT GENERATOR")
    print("=" * 60)

    # ── Ensure output directories exist ──────────────────────────────────
    results_dir = BASE_DIR / "results"
    graficos_dir = results_dir / "graficos"
    results_dir.mkdir(parents=True, exist_ok=True)
    graficos_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {results_dir}")

    # ── Collect all experiment data ───────────────────────────────────────
    print("\nLoading experiments...")
    records = collect_all_experiments()
    print(f"\nTotal experiments loaded: {len(records)}")

    if not records:
        print("[ERROR] No experiments found. Check directory structure and CSV files.")
        sys.exit(1)

    # ── Generate plots ────────────────────────────────────────────────────
    print("\nGenerating plots...")

    plot_energy_by_intensity(records, graficos_dir / "energy_by_intensity.png")
    plot_requests_by_intensity(records, graficos_dir / "requests_by_intensity.png")
    plot_energy_efficiency(records, graficos_dir / "energy_efficiency.png")
    plot_failed_tx(records, graficos_dir / "failed_tx_comparison.png")
    plot_node_energy_breakdown(records, graficos_dir / "node_energy_breakdown.png")
    plot_pod_distribution_heatmap(
        records, graficos_dir / "pod_distribution_heatmap.png"
    )

    # ── Generate text report ─────────────────────────────────────────────
    print("\nGenerating report.txt ...")
    report_text = generate_report_text(records)
    report_path = results_dir / "report.txt"
    report_path.write_text(report_text, encoding="utf-8")
    print(f"  Saved: {report_path}")

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("DONE")
    print(f"  Experiments processed : {len(records)}")
    print(f"  Report                : {report_path}")
    print(f"  Plots directory       : {graficos_dir}")
    graficos = sorted(graficos_dir.glob("*.png"))
    for g in graficos:
        print(f"    {g.name}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
