import csv
import argparse
import os
from math import isnan, isfinite
import sys, os
import matplotlib.pyplot as plt
import re

"""
app.py

Compare two gPROMS-organized CSV datasets and plot a_abs_profile(i,4) values.
Produces a CSV of differences, prints a short summary, and creates plots.

Usage:
    python app.py path/to/a_abs_profile_MEA.csv path/to/a_abs_profile_MEA-MEA.csv [--abs-tol 1e-12] [--rel-tol 1e-6] [--out diffs.csv]
"""


def parse_variables_csv(path):
    """
    Parse a CSV with lines containing variables like a_abs_profile(i,j):
      variable,value,lower,upper,type,units
    Special handling for parentheses that contain commas.
    Returns dict: variable -> dict with raw fields and numeric value if convertible.
    Skips empty/malformed lines.
    """
    vars_dict = {}
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            
            # Handle variables with parentheses containing commas like a_abs_profile(1,4)
            # Find the end of the variable name (after closing parenthesis)
            if '(' in line and ')' in line:
                paren_end = line.find(')')
                if paren_end != -1:
                    name = line[:paren_end+1]  # Include the closing parenthesis
                    rest = line[paren_end+1:]   # Everything after the closing parenthesis
                    if rest.startswith(','):
                        rest = rest[1:]  # Remove the leading comma
                    
                    # Parse the remaining fields
                    parts = rest.split(',')
                    if len(parts) >= 1:
                        # pad to 5 more columns (value, lower, upper, type, units)
                        parts = (parts + [""] * 5)[:5]
                        val_str, lower, upper, vtype, units = [p.strip() for p in parts]
                    else:
                        continue
                else:
                    # Fallback to regular CSV parsing
                    parts = line.split(',')
                    if len(parts) < 2:
                        continue
                    parts = (parts + [""] * 6)[:6]
                    name, val_str, lower, upper, vtype, units = [p.strip() for p in parts]
            else:
                # Regular CSV parsing for lines without parentheses
                parts = line.split(',')
                if len(parts) < 2:
                    continue
                parts = (parts + [""] * 6)[:6]
                name, val_str, lower, upper, vtype, units = [p.strip() for p in parts]
            
            if not name:
                continue
            
            num = None
            try:
                # allow scientific notation and decimals
                num = float(val_str)
                if not isfinite(num):
                    num = None
            except Exception:
                num = None
                
            vars_dict[name] = {
                "value_str": val_str,
                "value_num": num,
                "lower": lower,
                "upper": upper,
                "type": vtype,
                "units": units,
                "source_line": i,
            }
    return vars_dict

def format_sci(x):
    try:
        return f"{x:.16e}"
    except Exception:
        return ""

def compare_dicts(d1, d2, abs_tol=1e-12, rel_tol=1e-6):
    """
    Compare two parsed variable dicts.
    Returns list of diff rows (dicts) and summary counts.
    """
    keys = sorted(set(d1.keys()) | set(d2.keys()))
    diffs = []
    counts = {"only_in_1":0, "only_in_2":0, "equal_within_tol":0, "different":0}
    tiny = 1e-300
    for k in keys:
        a = d1.get(k)
        b = d2.get(k)
        row = {"variable": k}
        if a is None:
            row.update({
                "status": "only_in_2",
                "value1": "",
                "value2": b["value_str"],
                "abs_diff": "",
                "rel_diff": "",
                "in_tolerance": "false",
                "type1": "",
                "type2": b["type"],
                "units1": "",
                "units2": b["units"],
            })
            counts["only_in_2"] += 1
        elif b is None:
            row.update({
                "status": "only_in_1",
                "value1": a["value_str"],
                "value2": "",
                "abs_diff": "",
                "rel_diff": "",
                "in_tolerance": "false",
                "type1": a["type"],
                "type2": "",
                "units1": a["units"],
                "units2": "",
            })
            counts["only_in_1"] += 1
        else:
            row["type1"] = a["type"]
            row["type2"] = b["type"]
            row["units1"] = a["units"]
            row["units2"] = b["units"]
            row["value1"] = a["value_str"]
            row["value2"] = b["value_str"]
            n1 = a["value_num"]
            n2 = b["value_num"]
            if (n1 is not None) and (n2 is not None):
                abs_diff = abs(n1 - n2)
                denom = max(abs(n1), abs(n2), tiny)
                rel_diff = abs_diff / denom
                in_tol = (abs_diff <= abs_tol) or (rel_diff <= rel_tol)
                row["abs_diff"] = format_sci(abs_diff)
                row["rel_diff"] = f"{rel_diff:.6e}"
                row["in_tolerance"] = "true" if in_tol else "false"
                row["status"] = "equal_within_tol" if in_tol else "different"
                if in_tol:
                    counts["equal_within_tol"] += 1
                else:
                    counts["different"] += 1
            else:
                # non-numeric comparison: string equality
                equal = (a["value_str"].strip() == b["value_str"].strip())
                row["abs_diff"] = ""
                row["rel_diff"] = ""
                row["in_tolerance"] = "true" if equal else "false"
                row["status"] = "equal_within_tol" if equal else "different"
                if equal:
                    counts["equal_within_tol"] += 1
                else:
                    counts["different"] += 1
        diffs.append(row)
    return diffs, counts

def write_diffs_csv(path, diffs):
    header = ["variable","status","value1","value2","abs_diff","rel_diff","in_tolerance","type1","type2","units1","units2"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for r in diffs:
            writer.writerow([r.get(h,"") for h in header])

def extract_absorption_profiles_all_columns(vars_dict, pattern_name="a_abs_profile"):
    """
    Extract all a_abs_profile(i,j) values from parsed variables dictionary.
    Returns dict: {column: {stage_number: value}} for columns 1-4
    """
    profile_data = {1: {}, 2: {}, 3: {}, 4: {}}
    
    for var_name, var_info in vars_dict.items():
        # Look for the pattern a_abs_profile(stage,column) for all columns
        pattern = rf'{pattern_name}\((\d+),(\d+)\)'
        match = re.search(pattern, var_name)
        
        if match:
            stage_num = int(match.group(1))
            column_num = int(match.group(2))
            
            if column_num in [1, 2, 3, 4] and var_info["value_num"] is not None:
                profile_data[column_num][stage_num] = var_info["value_num"]
    
    return profile_data

def plot_absorption_profiles(d1, d2, file1_name, file2_name, plots_dir="analysis/results/plots"):
    """
    Plot and compare absorption profiles from two datasets with 4 subplots for each column.
    """
    # Extract profile data for all columns
    profiles1 = extract_absorption_profiles_all_columns(d1)
    profiles2 = extract_absorption_profiles_all_columns(d2)
    
    # Check if we have any data
    has_data = any(profiles1[col] for col in [1, 2, 3, 4]) or any(profiles2[col] for col in [1, 2, 3, 4])
    if not has_data:
        print("No absorption profile data found in either dataset.")
        return
    
    # Create plots directory if it doesn't exist
    os.makedirs(plots_dir, exist_ok=True)
    
    # Create figure with 4 subplots (2x2 grid)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Absorption Profile Comparison: {file1_name} vs {file2_name}\n(All 4 Columns)', 
                 fontsize=16, fontweight='bold')
    
    # Column titles and descriptions
    column_info = {
        1: "Liquid Outlet Temperature [K]",
        2: "Gas Outlet Flow Rate [kmol/s]", 
        3: "Liquid Outlet Flow Rate [kmol/s]",
        4: "CO2 Loading in Liquid Outlet [kmol CO2/kmol Absorbent]"
    }
    
    # Plot each column in its own subplot
    subplot_positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    
    for idx, col in enumerate([1, 2, 3, 4]):
        row, col_pos = subplot_positions[idx]
        ax = axes[row, col_pos]
        
        # Get data for this column
        profile1_col = profiles1[col]
        profile2_col = profiles2[col]
        
        # Convert to sorted lists for plotting
        stages1 = sorted(profile1_col.keys()) if profile1_col else []
        values1 = [profile1_col[stage] for stage in stages1] if profile1_col else []
        
        stages2 = sorted(profile2_col.keys()) if profile2_col else []
        values2 = [profile2_col[stage] for stage in stages2] if profile2_col else []
        
        # Plot data if available
        if stages1 and values1:
            ax.plot(stages1, values1, 'b-o', linewidth=2, markersize=4, 
                   label=f'{file1_name}', alpha=0.8)
        
        if stages2 and values2:
            ax.plot(stages2, values2, 'r-s', linewidth=2, markersize=4, 
                   label=f'{file2_name}', alpha=0.8)
        
        # Customize subplot
        ax.set_xlabel('Stage Number', fontsize=10, fontweight='bold')
        ax.set_ylabel('Value', fontsize=10, fontweight='bold')
        ax.set_title(f'{column_info[col]}', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.001, linestyle='--')
        ax.legend(fontsize=9)
        
        # Set axis limits with padding if we have data
        all_values = values1 + values2
        if all_values:
            y_min, y_max = min(all_values), max(all_values)
            y_range = y_max - y_min
            if y_range > 0:
                ax.set_ylim(y_min - 0.05*y_range, y_max + 0.05*y_range)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot with descriptive filename
    plot_filename = os.path.join(plots_dir, f'absorption_profiles_4columns_{file1_name}_vs_{file2_name}.png')
    plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
    print(f"4-column subplot saved as '{plot_filename}'")
    
    # Show the plot
    plt.show()
    
    # Print detailed comparison for each column
    print(f"\nAbsorption Profile Summary (All Columns):")
    
    # Save detailed comparison to CSV file in results directory
    csv_dir = "analysis/results/csv"
    os.makedirs(csv_dir, exist_ok=True)
    
    # Create separate CSV files for each column
    for col in [1, 2, 3, 4]:
        profile1_col = profiles1[col]
        profile2_col = profiles2[col]
        
        if not profile1_col and not profile2_col:
            continue
            
        stages1 = sorted(profile1_col.keys()) if profile1_col else []
        values1 = [profile1_col[stage] for stage in stages1] if profile1_col else []
        
        stages2 = sorted(profile2_col.keys()) if profile2_col else []
        values2 = [profile2_col[stage] for stage in stages2] if profile2_col else []
        
        print(f"\nColumn {col} - {column_info[col]}:")
        print(f"{file1_name}:")
        print(f"  - Stages: {len(stages1)} (from {min(stages1) if stages1 else 'N/A'} to {max(stages1) if stages1 else 'N/A'})")
        print(f"  - Value range: {min(values1):.6f} to {max(values1):.6f}" if values1 else "  - No data found")
        
        print(f"{file2_name}:")
        print(f"  - Stages: {len(stages2)} (from {min(stages2) if stages2 else 'N/A'} to {max(stages2) if stages2 else 'N/A'})")
        print(f"  - Value range: {min(values2):.6f} to {max(values2):.6f}" if values2 else "  - No data found")
        
        # Create CSV for this column
        comparison_csv = os.path.join(csv_dir, f'absorption_profile_column{col}_{file1_name}_vs_{file2_name}.csv')
        
        # Detailed stage-by-stage comparison
        all_stages = sorted(set(stages1 + stages2))
        if all_stages:
            print(f"\nDetailed Stage Comparison (Column {col}):")
            print(f"{'Stage':<6} {file1_name:<15} {file2_name:<15} {'Difference':<15}")
            print("-" * 60)
            
            # Prepare data for CSV export
            comparison_data = []
            comparison_data.append(['Stage', file1_name, file2_name, 'Difference', 'Abs_Difference', 'Rel_Difference'])
            
            for stage in all_stages:
                val1 = profile1_col.get(stage, None)
                val2 = profile2_col.get(stage, None)
                
                if val1 is not None and val2 is not None:
                    diff = val1 - val2
                    abs_diff = abs(diff)
                    rel_diff = abs_diff / max(abs(val1), abs(val2), 1e-12) * 100  # Percentage
                    
                    print(f"{stage:<6} {val1:<15.6f} {val2:<15.6f} {diff:<15.6f}")
                    comparison_data.append([stage, f"{val1:.10f}", f"{val2:.10f}", f"{diff:.10f}", f"{abs_diff:.10f}", f"{rel_diff:.4f}%"])
                elif val1 is not None:
                    print(f"{stage:<6} {val1:<15.6f} {'N/A':<15} {'N/A':<15}")
                    comparison_data.append([stage, f"{val1:.10f}", "N/A", "N/A", "N/A", "N/A"])
                elif val2 is not None:
                    print(f"{stage:<6} {'N/A':<15} {val2:<15.6f} {'N/A':<15}")
                    comparison_data.append([stage, "N/A", f"{val2:.10f}", "N/A", "N/A", "N/A"])
            
            # Write comparison to CSV
            with open(comparison_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(comparison_data)
            
            print(f"Column {col} comparison saved to '{comparison_csv}'")

def print_summary(counts, total):
    print("Comparison summary:")
    print(f"  Total variables considered: {total}")
    print(f"  Only in first file: {counts['only_in_1']}")
    print(f"  Only in second file: {counts['only_in_2']}")
    print(f"  Equal within tolerances: {counts['equal_within_tol']}")
    print(f"  Different: {counts['different']}")

def main():
    parser = argparse.ArgumentParser(description="Compare two gPROMS-organized CSV files and plot absorption profiles.")
    parser.add_argument("file1", help="Path to first CSV (e.g. a_abs_profile_MEA.csv)")
    parser.add_argument("file2", help="Path to second CSV (e.g. a_abs_profile_MEA-MEA.csv)")
    parser.add_argument("--abs-tol", type=float, default=1e-12, help="Absolute tolerance for numeric comparison")
    parser.add_argument("--rel-tol", type=float, default=1e-6, help="Relative tolerance for numeric comparison")
    parser.add_argument("--out", default="differences.csv", help="Output CSV path for differences")
    parser.add_argument("--plot-only", action="store_true", help="Only create plots, skip difference analysis")
    args = parser.parse_args()

    # Parse both CSV files
    print(f"Reading {args.file1}...")
    d1 = parse_variables_csv(args.file1)
    print(f"Reading {args.file2}...")
    d2 = parse_variables_csv(args.file2)
    
    # Extract file names for labeling
    file1_name = os.path.splitext(os.path.basename(args.file1))[0]
    file2_name = os.path.splitext(os.path.basename(args.file2))[0]
    
    # Create absorption profile plots
    print("\n=== Creating Absorption Profile Plots ===")
    plot_absorption_profiles(d1, d2, file1_name, file2_name)
    
    # Perform detailed comparison unless plot-only mode
    if not args.plot_only:
        print("\n=== Performing Detailed Variable Comparison ===")
        diffs, counts = compare_dicts(d1, d2, abs_tol=args.abs_tol, rel_tol=args.rel_tol)
        
        # Create CSV results directory and save with descriptive filename
        csv_dir = "analysis/results/csv"
        os.makedirs(csv_dir, exist_ok=True)
        
        # Generate descriptive filename for the differences CSV
        diff_csv_filename = f"variable_differences_{file1_name}_vs_{file2_name}.csv"
        diff_csv_path = os.path.join(csv_dir, diff_csv_filename)
        
        write_diffs_csv(diff_csv_path, diffs)
        print_summary(counts, total=len(diffs))
        print(f"Wrote variable differences to: {diff_csv_path}")
    else:
        print("Skipping detailed comparison (--plot-only mode)")

if __name__ == "__main__":
    # Use the existing prepared CSV files with a_abs_profile(i,4) data
    FILE1 = r"c:\Users\mm5425\OneDrive - Imperial College London\Documents\gPROMS\python\analysis\inputs\a_abs_profile_MEA.csv"
    FILE2 = r"c:\Users\mm5425\OneDrive - Imperial College London\Documents\gPROMS\python\analysis\inputs\a_abs_profile_MEA-BLEND.csv"

    if not (os.path.exists(FILE1) and os.path.exists(FILE2)):
        print("Files not found:")
        print(f"  {FILE1}")
        print(f"  {FILE2}")
        print("Make sure the analysis/inputs directory exists with the prepared CSV files.")
        sys.exit(1)

    # Set up arguments for full comparison mode (plots + detailed variable comparison)
    sys.argv = [sys.argv[0], FILE1, FILE2, "--plot-only"]
    main()