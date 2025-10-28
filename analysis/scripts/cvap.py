
#!/usr/bin/env python3
"""Scalable comparer for multiple variables between two gSTORE run files.

Usage: python analysis/scripts/compare.py [run1.txt] [run2.txt]

If no args provided, defaults to:
  Finals_runs/MEA/run.txt
  Finals_runs/MEA_MEA/run.txt

The script extracts numeric values for variables listed in VARIABLES_TO_COMPARE,
computes absolute and percentage differences (file1 - file2), generates plots,
and writes detailed CSV outputs under analysis/results/flowsheet_comparison/.

To add new variables to compare, simply add them to the VARIABLES_TO_COMPARE list below.
"""

from __future__ import annotations

import os
import re
import csv
import argparse
import math
from typing import Optional, Dict, List, Tuple

import matplotlib.pyplot as plt

# =============================================================================
# CONFIGURATION: Add variables here to compare them automatically
# =============================================================================

# Simple variables (direct 1:1 comparison)
VARIABLES_TO_COMPARE = [
    'Plant.Absorber.Stage(1).C_vap_I("H2O")',
    'Plant.Absorber.Stage(1).C_liq_I("H2O")',
    'Plant.Absorber.Stage(1).C_vap_I("CO2")',
    'Plant.Absorber.Stage(1).C_liq_I("CO2")',
    'Plant.Absorber.Stage(1).C_vap_I("N2")',
    'Plant.Absorber.Stage(1).C_liq_I("N2")',
    'Plant.Absorber.Stage(1).C_vap_out("H2O")',
    'Plant.Absorber.Stage(1).C_liq_out("H2O")',
    'Plant.Absorber.Stage(1).C_vap_out("CO2")',
    'Plant.Absorber.Stage(1).C_liq_out("CO2")',
    'Plant.Absorber.Stage(1).C_vap_out("N2")',
    'Plant.Absorber.Stage(1).C_liq_out("N2")',
    'Plant.Absorber.Stage(1).kvap("H2O")',
    'Plant.Absorber.Stage(1).kvap("CO2")',
    'Plant.Absorber.Stage(1).kvap("N2")',
    'Plant.Absorber.Stage(1).kliq("H2O")',
    'Plant.Absorber.Stage(1).kliq("CO2")',
    'Plant.Absorber.Stage(1).kliq("N2")',
]

# Composite variables: sum multiple variables from file1 vs single variable in file2
# Format: "display_name": {
#     "file1_vars": ["var1", "var2", ...],  # Variables to sum from file1
#     "file2_var": "single_var"             # Single variable from file2
# }
COMPOSITE_COMPARISONS = {
    'Plant.Absorber.Stage(1).C_vap_I_total_abs': {
        "file1_vars": [
            'Plant.Absorber.Stage(1).C_vap_I("ABSORBENT_1")',
            'Plant.Absorber.Stage(1).C_vap_I("ABSORBENT_2")',
        ],
        "file2_var": 'Plant.Absorber.Stage(1).C_vap_I("ABSORBENT_1")'
    },
    'Plant.Absorber.Stage(1).C_liq_I_total_abs': {
        "file1_vars": [
            'Plant.Absorber.Stage(1).C_liq_I("ABSORBENT_1")',
            'Plant.Absorber.Stage(1).C_liq_I("ABSORBENT_2")',
        ],
        "file2_var": 'Plant.Absorber.Stage(1).C_liq_I("ABSORBENT_1")'
    },
    'Plant.Absorber.Stage(1).C_vap_out_total_abs': {
        "file1_vars": [
            'Plant.Absorber.Stage(1).C_vap_out("ABSORBENT_1")',
            'Plant.Absorber.Stage(1).C_vap_out("ABSORBENT_2")',
        ],
        "file2_var": 'Plant.Absorber.Stage(1).C_vap_out("ABSORBENT_1")'
    },
    'Plant.Absorber.Stage(1).C_liq_out_total_abs': {
        "file1_vars": [
            'Plant.Absorber.Stage(1).C_liq_out("ABSORBENT_1")',
            'Plant.Absorber.Stage(1).C_liq_out("ABSORBENT_2")',
        ],
        "file2_var": 'Plant.Absorber.Stage(1).C_liq_out("ABSORBENT_1")'
    },
    'Plant.Absorber.Stage(1).kliq_total_abs': {
        "file1_vars": [
            'Plant.Absorber.Stage(1).kliq("ABSORBENT_1")',
        ],
        "file2_var": 'Plant.Absorber.Stage(1).kliq("ABSORBENT_1")'
    },
    'Plant.Absorber.Stage(1).kvap_total_abs': {
        "file1_vars": [
            'Plant.Absorber.Stage(1).kvap("ABSORBENT_1")',
        ],
        "file2_var": 'Plant.Absorber.Stage(1).kvap("ABSORBENT_1")'
    }
}


def extract_variable_from_run(path: str, var: str) -> Optional[float]:
    """Scan a gSTORE run file and return the first numeric value found for var.

    Returns None if not found or not parseable.
    """
    if not os.path.exists(path):
        return None
    pattern = re.compile(r"^\s*" + re.escape(var) + r"\s*:\s*([+-]?[0-9.eE+ -]+)")
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            m = pattern.match(line)
            if m:
                token = m.group(1).strip()
                # remove spaces inside token if any
                token = token.replace(" ", "")
                try:
                    return float(token)
                except Exception:
                    return None
    return None


def extract_all_variables(path: str, variables: List[str]) -> Dict[str, Optional[float]]:
    """Extract all variables from a run file in one pass for efficiency."""
    results = {var: None for var in variables}
    if not os.path.exists(path):
        return results
    
    patterns = {var: re.compile(r"^\s*" + re.escape(var) + r"\s*:\s*([+-]?[0-9.eE+ -]+)") for var in variables}
    
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            for var, pattern in patterns.items():
                if results[var] is None:  # Only match if not found yet
                    m = pattern.match(line)
                    if m:
                        token = m.group(1).strip().replace(" ", "")
                        try:
                            results[var] = float(token)
                        except Exception:
                            pass
    return results


def get_all_unique_variables() -> List[str]:
    """Get all unique variables needed from both simple and composite comparisons."""
    all_vars = set(VARIABLES_TO_COMPARE)
    
    # Add variables from composite comparisons
    for comp_name, comp_def in COMPOSITE_COMPARISONS.items():
        all_vars.update(comp_def["file1_vars"])
        all_vars.add(comp_def["file2_var"])
    
    return list(all_vars)


def compute_composite_values(values: Dict[str, Optional[float]], is_file1: bool) -> Dict[str, Optional[float]]:
    """Compute composite values based on the configuration."""
    composite_results = {}
    
    for comp_name, comp_def in COMPOSITE_COMPARISONS.items():
        if is_file1:
            # Sum the file1_vars
            file1_vars = comp_def["file1_vars"]
            sum_val = 0.0
            all_present = True
            for var in file1_vars:
                val = values.get(var)
                if val is None:
                    all_present = False
                    break
                sum_val += val
            composite_results[comp_name] = sum_val if all_present else None
        else:
            # Use the single file2_var
            file2_var = comp_def["file2_var"]
            composite_results[comp_name] = values.get(file2_var)
    
    return composite_results


def ensure_outdir() -> str:
    out = os.path.join("analysis", "results", "flowsheet_comparison")
    os.makedirs(out, exist_ok=True)
    return out


def compute_differences(v1: Optional[float], v2: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    """Compute absolute and percentage differences. Returns (abs_diff, pct_diff)."""
    if v1 is None or v2 is None:
        return None, None
    
    abs_diff = v1 - v2
    if abs(v2) < 1e-12:
        pct_diff = float('inf') if abs_diff != 0 else 0.0
    else:
        pct_diff = (abs_diff / v2) * 100.0
    
    return abs_diff, pct_diff


def write_comparison_csv(outdir: str, file1: str, file2: str, 
                        values1: Dict[str, Optional[float]], 
                        values2: Dict[str, Optional[float]],
                        composite1: Dict[str, Optional[float]],
                        composite2: Dict[str, Optional[float]]) -> str:
    """Write detailed CSV with all variable comparisons."""
    out_csv = os.path.join(outdir, "cvap.csv")
    
    with open(out_csv, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["variable", "type", "file1_value", "file2_value", "abs_diff", "pct_diff(%)", "file1_path", "file2_path"])
        
        # Write simple variables
        for var in VARIABLES_TO_COMPARE:
            v1 = values1.get(var)
            v2 = values2.get(var)
            abs_diff, pct_diff = compute_differences(v1, v2)
            
            writer.writerow([
                var,
                "simple",
                f"{v1:.16e}" if v1 is not None else "",
                f"{v2:.16e}" if v2 is not None else "",
                f"{abs_diff:.16e}" if abs_diff is not None else "",
                f"{pct_diff:.6f}" if pct_diff is not None and not math.isinf(pct_diff) else ("inf" if pct_diff == float('inf') else ""),
                os.path.basename(file1),
                os.path.basename(file2)
            ])
        
        # Write composite variables
        for comp_name in COMPOSITE_COMPARISONS.keys():
            v1 = composite1.get(comp_name)
            v2 = composite2.get(comp_name)
            abs_diff, pct_diff = compute_differences(v1, v2)
            
            writer.writerow([
                comp_name,
                "composite",
                f"{v1:.16e}" if v1 is not None else "",
                f"{v2:.16e}" if v2 is not None else "",
                f"{abs_diff:.16e}" if abs_diff is not None else "",
                f"{pct_diff:.6f}" if pct_diff is not None and not math.isinf(pct_diff) else ("inf" if pct_diff == float('inf') else ""),
                os.path.basename(file1),
                os.path.basename(file2)
            ])
    
    return out_csv


def plot_percentage_differences(outdir: str, file1: str, file2: str,
                               values1: Dict[str, Optional[float]], 
                               values2: Dict[str, Optional[float]],
                               composite1: Dict[str, Optional[float]],
                               composite2: Dict[str, Optional[float]]) -> str:
    """Generate a bar plot of percentage differences."""
    variables = []
    pct_diffs = []
    
    # Add simple variables
    for var in VARIABLES_TO_COMPARE:
        v1 = values1.get(var)
        v2 = values2.get(var)
        _, pct_diff = compute_differences(v1, v2)
        
        if pct_diff is not None and not math.isinf(pct_diff):
            variables.append(var.replace("Plant.", ""))  # Clean up names for display
            pct_diffs.append(pct_diff)
    
    # Add composite variables
    for comp_name in COMPOSITE_COMPARISONS.keys():
        v1 = composite1.get(comp_name)
        v2 = composite2.get(comp_name)
        _, pct_diff = compute_differences(v1, v2)
        
        if pct_diff is not None and not math.isinf(pct_diff):
            variables.append(f"{comp_name}")
            pct_diffs.append(pct_diff)
    
    if not variables:
        print("No valid percentage differences to plot.")
        return ""
    
    # Create plot
    plt.figure(figsize=(max(10, len(variables) * 0.8), 6))
    bars = plt.bar(range(len(variables)), pct_diffs)
    
    # Color bars: negative = red, positive = green, zero = blue
    for i, (bar, pct) in enumerate(zip(bars, pct_diffs)):
        if pct < -1:
            bar.set_color('lightblue')
        elif pct > 1:
            bar.set_color('lightblue')
        else:
            bar.set_color('lightblue')
    
    # Add percentage value labels on top/bottom of bars
    for i, (bar, pct) in enumerate(zip(bars, pct_diffs)):
        height = bar.get_height()
        # Position label above bar if positive, below if negative
        if height >= 0:
            y_pos = height + max(abs(max(pct_diffs)), abs(min(pct_diffs))) * 0.01  # Small offset above
            va = 'bottom'
        else:
            y_pos = height - max(abs(max(pct_diffs)), abs(min(pct_diffs))) * 0.01  # Small offset below
            va = 'top'
        
        plt.text(i, y_pos, f'{pct:.1f}%', ha='center', va=va, fontsize=8, weight='bold')
    
    plt.axhline(0, color="black", linewidth=0.8, linestyle="-")
    plt.xticks(range(len(variables)), variables, rotation=45, ha='right')
    plt.ylabel("Percentage Difference (%) (MEA_MEA - MEA) / MEA)")
    plt.title(f"Variable Differences: MEA_MEA vs MEA")
    plt.ylim(-100, 100)
    plt.grid(True, alpha=0.0001)
    plt.tight_layout()
    
    out_png = os.path.join(outdir, "cvap.png")
    plt.savefig(out_png, dpi=150)
    plt.close()
    
    return out_png



def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run1", nargs="?", default=os.path.join("Finals_runs", "MEA_BLEND", "run.txt"),
                       help="First run file to compare")
    parser.add_argument("run2", nargs="?", default=os.path.join("Finals_runs", "MEA", "run.txt"),
                       help="Second run file to compare")
    parser.add_argument("--no-plot", action="store_true", help="Skip generating plots")
    args = parser.parse_args()

    p1 = args.run1
    p2 = args.run2
    
    # Get all variables needed
    all_vars = get_all_unique_variables()
    
    print(f"Extracting {len(VARIABLES_TO_COMPARE)} simple + {len(COMPOSITE_COMPARISONS)} composite variables from:")
    print(f"  File1: {p1}")
    print(f"  File2: {p2}")

    # Extract raw variables
    values1 = extract_all_variables(p1, all_vars)
    values2 = extract_all_variables(p2, all_vars)
    
    # Compute composite values
    composite1 = compute_composite_values(values1, is_file1=True)
    composite2 = compute_composite_values(values2, is_file1=False)

    outdir = ensure_outdir()
    
    # Write CSV
    out_csv = write_comparison_csv(outdir, p1, p2, values1, values2, composite1, composite2)
    print(f"\nDetailed CSV written to: {out_csv}")
    
    # Generate plot
    if not args.no_plot:
        out_png = plot_percentage_differences(outdir, p1, p2, values1, values2, composite1, composite2)
        if out_png:
            print(f"Plot saved to: {out_png}")


if __name__ == '__main__':
    main()

