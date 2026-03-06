#!/usr/bin/env python3
"""
analyze_node_distribution.py
============================
Analyzes pod distribution per node in Kubernetes experiments.

For each experiment directory that contains a node_distribution/ folder,
this script reads kps_crictl_ps_all.txt, counts how many instances of each
pod type landed on each node, and writes a node_distribution.csv summary.

Usage:
    python analyze_node_distribution.py --fase fase3
    python analyze_node_distribution.py --fase fase1

The --fase argument filters which phase subdirectories to process.
Only node_distribution/ folders whose path contains the fase string are included.

Base directory (hardcoded):
    /home/josec/green_computing/microservices/historyexecutions/
    experiments-data/plugin-comparation/

Output:
    node_distribution/node_distribution.csv  (one per processed experiment)

Author: TARS (assisted by Claude Code)
Date: 2026-02-21
"""

import re
import csv
import argparse
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_DIR = Path(
    "/home/josec/green_computing/microservices/historyexecutions/"
    "experiments-data/plugin-comparation/"
)

# Canonical node names in display order (rows in output CSV)
CANONICAL_NODES = ["nitro5", "aspire", "scorpius", "leo"]

# TeaStore service pod names — exact strings as they appear in the NAME field.
# Order here defines column order in the output CSV.
TEASTORE_PODS = [
    "teastore-webui",
    "teastore-image",
    "teastore-db",
    "teastore-registry",
    "teastore-auth",
    "teastore-recommender",
    "teastore-persistence",
]

# CSV column order: node + teastore pods + system bucket
CSV_COLUMNS = ["node"] + TEASTORE_PODS + ["own-k8s"]

# Regex to extract the container NAME field.
# The CREATED column can span multiple words ("About a minute ago", "8 hours ago"),
# so positional column splitting is unreliable.
# Strategy: find "Running" then capture the very next non-whitespace token.
RUNNING_NAME_RE = re.compile(r"Running\s+(\S+)")

# Regex to detect a node section header, e.g.:
#   ### NODO: luish-Nitro-AN515-57 (LOCAL) ###
#   ### NODO: luish@luish-Aspire-A315-55G ###
NODE_HEADER_RE = re.compile(r"^###\s+NODO:\s+(.+?)\s*###")


# ---------------------------------------------------------------------------
# Helper: map raw header string → canonical node name
# ---------------------------------------------------------------------------

def canonical_node_name(raw_header: str) -> str | None:
    """
    Map the raw NODO header string to one of the four canonical names.

    Matching is case-insensitive and based on substring presence:
      - "Nitro"   → nitro5
      - "Aspire"  → aspire
      - "scorpius"→ scorpius
      - "leo"     → leo

    Returns None if the header does not match any known node,
    which would be a data anomaly worth logging but not crashing over.

    Parameters
    ----------
    raw_header : str
        The string captured between "### NODO: " and " ###".

    Returns
    -------
    str | None
        Canonical node name or None if unrecognised.
    """
    lower = raw_header.lower()
    if "nitro" in lower:
        return "nitro5"
    if "aspire" in lower:
        return "aspire"
    if "scorpius" in lower:
        return "scorpius"
    if "leo" in lower:
        return "leo"
    return None


# ---------------------------------------------------------------------------
# Helper: classify a container NAME into pod-type bucket
# ---------------------------------------------------------------------------

def classify_pod(name: str) -> str:
    """
    Return the pod-type bucket for a given container NAME string.

    If the name matches one of the seven teastore service names exactly,
    that name is returned as-is.  Everything else (coredns, calico-node,
    kube-proxy, energy-scheduler, etcd, kube-apiserver, etc.) is bucketed
    into the aggregate "own-k8s" category.

    Parameters
    ----------
    name : str
        The container NAME field extracted from a crictl ps line.

    Returns
    -------
    str
        Either a teastore pod name or "own-k8s".
    """
    if name in TEASTORE_PODS:
        return name
    return "own-k8s"


# ---------------------------------------------------------------------------
# Core parser: read one kps_crictl_ps_all.txt → distribution dict
# ---------------------------------------------------------------------------

def parse_kps_crictl(txt_path: Path) -> dict[str, dict[str, int]]:
    """
    Parse a kps_crictl_ps_all.txt file and count pod instances per node.

    The file structure alternates between node section headers
    (lines matching NODE_HEADER_RE) and container rows (lines containing
    "Running").  A header line resets the current node context; subsequent
    Running lines are attributed to that node until the next header.

    The CONTAINER / IMAGE / ... header line is safely ignored because it
    does not contain the literal word "Running".

    Parameters
    ----------
    txt_path : Path
        Absolute path to the kps_crictl_ps_all.txt file.

    Returns
    -------
    dict[str, dict[str, int]]
        Nested dict: { canonical_node → { pod_type → count } }.
        All four canonical nodes are always present (even if count = 0).
        All CSV_COLUMNS keys (excluding "node") are present per node.
    """
    # Initialise counters for all four nodes and all pod types to 0.
    # Using defaultdict(int) under the hood but pre-populating so zeros
    # are guaranteed in the output even for absent nodes.
    counts: dict[str, dict[str, int]] = {
        node: {col: 0 for col in CSV_COLUMNS if col != "node"}
        for node in CANONICAL_NODES
    }

    current_node: str | None = None  # canonical name of the node being parsed

    with txt_path.open(encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.rstrip()

            # -- Check for a NODO section header ----------------------------
            header_match = NODE_HEADER_RE.match(line)
            if header_match:
                raw_header = header_match.group(1)
                current_node = canonical_node_name(raw_header)
                if current_node is None:
                    # Unknown node: log and reset context so we skip its rows
                    print(f"  [WARN] Unrecognised node header: '{raw_header}' "
                          f"in {txt_path}")
                continue  # header lines have no container data

            # -- Check for a Running container row --------------------------
            running_match = RUNNING_NAME_RE.search(line)
            if running_match and current_node is not None:
                pod_name = running_match.group(1)
                bucket = classify_pod(pod_name)
                counts[current_node][bucket] += 1

    return counts


# ---------------------------------------------------------------------------
# Writer: dump counts dict → node_distribution.csv
# ---------------------------------------------------------------------------

def write_csv(out_path: Path, counts: dict[str, dict[str, int]]) -> None:
    """
    Write the pod-count dictionary to a CSV file.

    Rows are written in CANONICAL_NODES order (nitro5, aspire, scorpius, leo).
    Columns follow CSV_COLUMNS order exactly as specified in the task.

    Overwrites any existing file at out_path without prompting.

    Parameters
    ----------
    out_path : Path
        Destination path for the CSV file.
    counts : dict[str, dict[str, int]]
        Output of parse_kps_crictl().
    """
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for node in CANONICAL_NODES:
            row = {"node": node}
            row.update(counts[node])  # merge all pod-type counts into row
            writer.writerow(row)


# ---------------------------------------------------------------------------
# Discovery: find all node_distribution/ dirs matching the requested fase
# ---------------------------------------------------------------------------

def find_node_distribution_dirs(fase: str) -> list[Path]:
    """
    Recursively search BASE_DIR for directories named 'node_distribution'
    whose path contains the fase string (e.g. "fase3").

    The search is case-sensitive because the directory names in this project
    follow a consistent lowercase naming convention.

    Parameters
    ----------
    fase : str
        Phase filter string, e.g. "fase3".

    Returns
    -------
    list[Path]
        Sorted list of matching node_distribution/ directories.
    """
    matches = []
    # rglob("node_distribution") matches directories with that exact name
    for nd_dir in BASE_DIR.rglob("node_distribution"):
        if not nd_dir.is_dir():
            continue
        # Filter: the path (as a string) must contain the fase substring
        if fase in str(nd_dir):
            matches.append(nd_dir)
    return sorted(matches)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    CLI entry point.  Parses arguments, discovers experiment directories,
    processes each one, and reports summary counts.
    """
    # -- Argument parsing ---------------------------------------------------
    parser = argparse.ArgumentParser(
        description=(
            "Analyse pod distribution per node from kps_crictl_ps_all.txt "
            "files and write node_distribution.csv per experiment."
        )
    )
    parser.add_argument(
        "--fase",
        choices=["fase1", "fase2", "fase3"],
        default="fase3",
        help="Phase to process (default: fase3).  "
             "Only experiments whose path contains this string are included.",
    )
    args = parser.parse_args()

    print(f"\n[TARS] Scanning for node_distribution/ directories under:")
    print(f"       {BASE_DIR}")
    print(f"[TARS] Phase filter: '{args.fase}'\n")

    # -- Discovery ----------------------------------------------------------
    nd_dirs = find_node_distribution_dirs(args.fase)

    if not nd_dirs:
        print(f"[TARS] No node_distribution/ directories found for "
              f"'{args.fase}'. Nothing to do.")
        return

    print(f"[TARS] Found {len(nd_dirs)} node_distribution/ director"
          f"{'y' if len(nd_dirs) == 1 else 'ies'} to process.\n")

    processed = 0
    skipped = 0

    # -- Processing loop ----------------------------------------------------
    for nd_dir in nd_dirs:
        # Build a human-readable experiment label from the path.
        # e.g. "without-plugin/fase3/exp(04:42:15)_fase3_low_iter1"
        try:
            rel_label = nd_dir.parent.relative_to(BASE_DIR)
        except ValueError:
            rel_label = nd_dir.parent  # fallback: use the full path

        txt_path = nd_dir / "kps_crictl_ps_all.txt"
        csv_path = nd_dir / "node_distribution.csv"

        print(f"[-->] Processing: {rel_label}")

        # -- Guard: input file must exist -----------------------------------
        if not txt_path.exists():
            print(f"  [WARN] kps_crictl_ps_all.txt not found — skipping.\n")
            skipped += 1
            continue

        # -- Parse and write ------------------------------------------------
        counts = parse_kps_crictl(txt_path)
        write_csv(csv_path, counts)

        # -- Human-readable summary of what was found -----------------------
        for node in CANONICAL_NODES:
            ts_count = sum(
                counts[node][p] for p in TEASTORE_PODS
            )
            k8s_count = counts[node]["own-k8s"]
            ts_detail = ", ".join(
                f"{p.replace('teastore-', '')}={counts[node][p]}"
                for p in TEASTORE_PODS
                if counts[node][p] > 0
            ) or "none"
            print(f"  {node:10s}: {ts_count} teastore ({ts_detail})"
                  f", {k8s_count} k8s-system")

        print(f"  [OK]  Written → {csv_path}\n")
        processed += 1

    # -- Final summary ------------------------------------------------------
    print(f"[TARS] Done.  Processed: {processed}  |  Skipped: {skipped}  "
          f"|  Total found: {len(nd_dirs)}")


# ---------------------------------------------------------------------------
# Script guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
