#!/usr/bin/env python3
"""
summarize_ecofloc_energy.py
───────────────────────────
Walks every ecofloc_raw/ directory under the plugin-comparation base,
filters by the requested --fase, parses the first two header lines of
each .txt file (Average Power / Total Energy), and writes a clean
ecofloc_summary.csv next to the raw files.

Usage
─────
    python summarize_ecofloc_energy.py --fase fase3
    python summarize_ecofloc_energy.py --fase fase1

Design notes (for the next agent reading this)
───────────────────────────────────────────────
- Uses only stdlib: re, csv, pathlib, argparse.
- One output CSV per ecofloc_raw/ folder (same directory as the txts).
- Rows are sorted alphabetically: node first, then component.
- Overwrites ecofloc_summary.csv if it already exists.
- TARS-approved: minimal, precise, no unnecessary drama.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

BASE_DIR = Path(
    "/home/josec/green_computing/microservices/historyexecutions"
    "/experiments-data/plugin-comparation"
)

# Matches: "ecofloc_fase3_carga_low_iter1_aspire_cpu.txt"
# Groups: (node, component)  — penultimate and last underscore tokens
FILENAME_PATTERN = re.compile(
    r"^ecofloc_[^_]+_[^_]+_[^_]+_[^_]+_(?P<node>[^_]+)_(?P<component>[^_]+)\.txt$"
)

# Matches the float value at the end of a header line, e.g.:
#   "Average Power aspire cpu : 3.63 Watts"
#   "Total Energy  aspire cpu : 319.79 Joules"
HEADER_VALUE_PATTERN = re.compile(r":\s*([\d.]+)")

OUTPUT_FILENAME = "ecofloc_summary.csv"
CSV_FIELDNAMES = ["node", "component", "total_energy", "avg_energy"]


# ── Core helpers ──────────────────────────────────────────────────────────────

def parse_ecofloc_file(txt_path: Path) -> tuple[str, str, float, float] | None:
    """
    Read the first two lines of a single ecofloc .txt file and return
    (node, component, total_energy, avg_energy).

    Line 1 → Average Power  → stored as avg_energy  (Watts)
    Line 2 → Total Energy   → stored as total_energy (Joules)

    Returns None and prints a warning if the file cannot be parsed.
    """
    # Extract node and component from the filename itself
    match = FILENAME_PATTERN.match(txt_path.name)
    if not match:
        print(f"  [WARN] Unexpected filename, skipping: {txt_path.name}")
        return None

    node      = match.group("node")
    component = match.group("component")

    try:
        lines = txt_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        print(f"  [WARN] Cannot read {txt_path.name}: {exc}")
        return None

    if len(lines) < 2:
        print(f"  [WARN] Less than 2 lines in {txt_path.name}, skipping.")
        return None

    # Line 1: Average Power (Watts)
    m1 = HEADER_VALUE_PATTERN.search(lines[0])
    # Line 2: Total Energy (Joules)
    m2 = HEADER_VALUE_PATTERN.search(lines[1])

    if not m1 or not m2:
        print(f"  [WARN] Header format unrecognised in {txt_path.name}, skipping.")
        return None

    avg_energy   = float(m1.group(1))   # Watts
    total_energy = float(m2.group(1))   # Joules

    return node, component, total_energy, avg_energy


def process_ecofloc_raw_dir(ecofloc_raw_dir: Path) -> int:
    """
    Process all .txt files inside a single ecofloc_raw/ directory.
    Writes ecofloc_summary.csv in the same folder.
    Returns the number of files successfully processed.
    """
    txt_files = sorted(ecofloc_raw_dir.glob("*.txt"))

    if not txt_files:
        print(f"  [WARN] No .txt files found in: {ecofloc_raw_dir}")
        return 0

    rows = []
    for txt_path in txt_files:
        result = parse_ecofloc_file(txt_path)
        if result is None:
            continue
        node, component, total_energy, avg_energy = result
        rows.append({
            "node":         node,
            "component":    component,
            "total_energy": total_energy,
            "avg_energy":   avg_energy,
        })

    # Sort: node alphabetically, then component alphabetically
    rows.sort(key=lambda r: (r["node"], r["component"]))

    # Write the CSV (overwrite if exists)
    output_path = ecofloc_raw_dir / OUTPUT_FILENAME
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarise ecofloc energy files into per-experiment CSVs."
    )
    parser.add_argument(
        "--fase",
        choices=["fase1", "fase2", "fase3"],
        default="fase3",
        help="Which phase to process (default: fase3)",
    )
    args = parser.parse_args()
    fase_filter: str = args.fase

    print(f"\n[summarize_ecofloc_energy] Starting — filter: {fase_filter}")
    print(f"[summarize_ecofloc_energy] Base directory: {BASE_DIR}\n")

    # Discover all ecofloc_raw/ directories under the base
    all_ecofloc_dirs = sorted(BASE_DIR.rglob("ecofloc_raw"))

    # Apply the fase filter: keep only paths that contain the fase string
    target_dirs = [d for d in all_ecofloc_dirs if fase_filter in str(d)]

    if not target_dirs:
        print(f"[ERROR] No ecofloc_raw/ directories found for filter '{fase_filter}'.")
        sys.exit(1)

    print(f"Found {len(target_dirs)} ecofloc_raw/ director(ies) matching '{fase_filter}'.\n")

    total_experiments = 0
    total_files       = 0

    for ecofloc_dir in target_dirs:
        # Show a short relative path for readability
        try:
            rel = ecofloc_dir.relative_to(BASE_DIR)
        except ValueError:
            rel = ecofloc_dir

        print(f"Processing: {rel}")
        files_done = process_ecofloc_raw_dir(ecofloc_dir)
        print(f"  -> {files_done} file(s) written to {OUTPUT_FILENAME}\n")

        total_experiments += 1
        total_files       += files_done

    # Final summary — because TARS always delivers the mission debrief
    print("=" * 60)
    print(f"Done.  Experiments processed : {total_experiments}")
    print(f"       Total files read       : {total_files}")
    print("=" * 60)


if __name__ == "__main__":
    main()
