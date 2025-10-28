#!/usr/bin/env python3
"""Compare two flowsheet result CSVs and plot differences.

Reads two files (default: analysis/inputs/flowsheet_results/MEA.csv
and analysis/inputs/flowsheet_results/MEA_MEA.csv), computes numeric
differences for common variables, handles the case where one file
contains two absorbent entries (ABSORBENT_1 and ABSORBENT_2) while
the other contains a single absorbent entry (treats the two as summed
and compares to the single), then writes a CSV summary and a PNG plot.

No external dependencies besides matplotlib (stdlib only otherwise).
"""
from __future__ import annotations

import argparse
import csv
import math
import os
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt


def read_flowsheet_csv(path: str) -> Dict[str, float]:
    d: Dict[str, float] = {}
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            # Split into name and value — the CSV format here is simple: name,value,...
            parts = line.split(",")
            name = parts[0]
            try:
                value = float(parts[1])
            except Exception:
                # If value cannot be parsed, skip
                continue
            d[name] = value
    return d


def ensure_dirs(base: str) -> Tuple[str, str]:
    csv_dir = os.path.join(base, "csv")
    plots_dir = os.path.join(base, "plots")
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    return csv_dir, plots_dir


def is_absorbent_key(key: str) -> bool:
    return "ABSORBENT" in key


def match_and_sum_absorbents(d1: Dict[str, float], d2: Dict[str, float], tol: float = 1e-8) -> Tuple[Dict[str, Tuple[Optional[float], Optional[float], str]], List[str], List[str]]:
    """
    Returns a mapping of variable -> (v1, v2, note) where combined absorbent pairs
    are handled: if one dict has two ABSORBENT keys and the other has one, we
    compare the sum to the single.

    Also returns lists of consumed keys from d1 and d2 so callers can avoid duplicating entries.
    """
    results: Dict[str, Tuple[Optional[float], Optional[float], str]] = {}
    consumed1: List[str] = []
    consumed2: List[str] = []

    # Quick absorbent keys
    abs1 = [k for k in d1.keys() if is_absorbent_key(k)]
    abs2 = [k for k in d2.keys() if is_absorbent_key(k)]

    # Helper to add a result entry
    def add_entry(name: str, v1: Optional[float], v2: Optional[float], note: str = ""):
        results[name] = (v1, v2, note)

    # If one file has two absorbent keys and the other has one, try to match sums
    if len(abs1) == 2 and len(abs2) == 1:
        s = d1[abs1[0]] + d1[abs1[1]]
        other_key = abs2[0]
        if math.isclose(s, d2[other_key], rel_tol=1e-8, abs_tol=tol):
            add_entry(other_key, s, d2[other_key], "sum of two absorbents in file1 vs single in file2")
            consumed1.extend(abs1)
            consumed2.append(other_key)

    if len(abs2) == 2 and len(abs1) == 1:
        s = d2[abs2[0]] + d2[abs2[1]]
        other_key = abs1[0]
        if math.isclose(s, d1[other_key], rel_tol=1e-8, abs_tol=tol):
            add_entry(other_key, d1[other_key], s, "single in file1 vs sum of two absorbents in file2")
            consumed2.extend(abs2)
            consumed1.append(other_key)

    return results, consumed1, consumed2


def build_comparisons(d1: Dict[str, float], d2: Dict[str, float]) -> List[Tuple[str, Optional[float], Optional[float], Optional[float], Optional[float], str]]:
    """Return list of tuples: (name, v1, v2, abs_diff, pct_diff, note)"""
    pre_map, consumed1, consumed2 = match_and_sum_absorbents(d1, d2)

    comps: List[Tuple[str, Optional[float], Optional[float], Optional[float], Optional[float], str]] = []

    # First add pre-mapped special entries
    for name, (v1, v2, note) in pre_map.items():
        if v1 is None or v2 is None:
            abs_diff = None
            pct_diff = None
        else:
            abs_diff = v1 - v2
            # Calculate percentage difference: ((v1 - v2) / v2) * 100
            # Handle case where v2 is zero or very small
            if abs(v2) < 1e-12:
                pct_diff = float('inf') if abs_diff != 0 else 0.0
            else:
                pct_diff = ((v1 - v2) / v2) * 100
        comps.append((name, v1, v2, abs_diff, pct_diff, note))

    # Build union of keys excluding consumed ones
    keys = set(d1.keys()) | set(d2.keys())
    for k in list(keys):
        if k in consumed1 or k in consumed2:
            continue
        v1 = d1.get(k)
        v2 = d2.get(k)
        note = ""
        if v1 is None or v2 is None:
            abs_diff = None
            pct_diff = None
        else:
            abs_diff = v1 - v2
            # Calculate percentage difference: ((v1 - v2) / v2) * 100
            # Handle case where v2 is zero or very small
            if abs(v2) < 1e-12:
                pct_diff = float('inf') if abs_diff != 0 else 0.0
            else:
                pct_diff = ((v1 - v2) / v2) * 100
        comps.append((k, v1, v2, abs_diff, pct_diff, note))

    # Sort by absolute percentage difference descending (missing values go last)
    comps.sort(key=lambda t: (abs(t[4]) if t[4] is not None and not math.isinf(t[4]) else -1), reverse=True)
    return comps


def write_csv(out_path: str, comps: List[Tuple[str, Optional[float], Optional[float], Optional[float], Optional[float], str]]):
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["variable", "value_file1", "value_file2", "abs_diff", "pct_diff", "note"])
        for name, v1, v2, abs_diff, pct_diff, note in comps:
            writer.writerow([
                name,
                "" if v1 is None else f"{v1:.16e}",
                "" if v2 is None else f"{v2:.16e}",
                "" if abs_diff is None else f"{abs_diff:.16e}",
                "" if pct_diff is None else f"{pct_diff:.2f}%",
                note,
            ])


def plot_differences(plot_path: str, comps: List[Tuple[str, Optional[float], Optional[float], Optional[float], Optional[float], str]], top_n: int = 40):
    # Choose entries where we have both values and pct_diff is not None and not infinite
    numeric = [c for c in comps if c[4] is not None and not math.isinf(c[4])]
    numeric = numeric[:top_n]
    if not numeric:
        print("No overlapping numeric variables to plot.")
        return

    names = [c[0] for c in numeric]
    pct_diffs = [c[4] for c in numeric]

    plt.figure(figsize=(max(8, len(names) * 0.25), 6))
    bars = plt.bar(range(len(names)), pct_diffs, color="tab:blue")
    plt.axhline(0, color="black", linewidth=0.6)
    plt.xticks(range(len(names)), names, rotation=90)
    plt.ylabel("Percentage difference (%) ((file1 - file2) / file2 * 100)")
    plt.title("Top percentage differences between flowsheet results (top %d)" % len(names))
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file1", nargs="?", default="analysis/inputs/flowsheet_results/MEA.csv", help="first flowsheet CSV")
    parser.add_argument("file2", nargs="?", default="analysis/inputs/flowsheet_results/MEA_MEA.csv", help="second flowsheet CSV")
    parser.add_argument("--outdir", default="analysis/results/flowsheet_comparison", help="output base directory")
    args = parser.parse_args()

    f1 = args.file1
    f2 = args.file2
    if not os.path.exists(f1):
        print(f"ERROR: file1 not found: {f1}")
        return
    if not os.path.exists(f2):
        print(f"ERROR: file2 not found: {f2}")
        return

    d1 = read_flowsheet_csv(f1)
    d2 = read_flowsheet_csv(f2)

    csv_dir, plots_dir = ensure_dirs(args.outdir)

    comps = build_comparisons(d1, d2)

    base1 = os.path.splitext(os.path.basename(f1))[0]
    base2 = os.path.splitext(os.path.basename(f2))[0]
    out_csv = os.path.join(csv_dir, f"flowsheet_comparison_{base1}_vs_{base2}.csv")
    out_png = os.path.join(plots_dir, f"flowsheet_comparison_{base1}_vs_{base2}.png")

    write_csv(out_csv, comps)
    plot_differences(out_png, comps)

    # Summaries
    total = len(comps)
    overlap = len([c for c in comps if c[4] is not None])
    print(f"Comparison written to: {out_csv}")
    print(f"Plot written to: {out_png}")
    print(f"Total variables considered: {total}, overlapping numeric comparisons: {overlap}")


if __name__ == "__main__":
    main()
