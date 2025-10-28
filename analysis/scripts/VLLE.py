#!/usr/bin/env python3
"""
VLLE (Vapor-Liquid-Liquid Equilibrium) Plotter for gSTORE run files.

Plots Plant.Absorber.Stage(i).btpflash_2(25), btpflash_2(17), and btpflash_2(9)
for each stage from Finals_runs/MEA_MEA_V2/run.txt.

These variables likely represent phase equilibrium data:
- btpflash_2(25): Phase data index 25
- btpflash_2(17): Phase data index 17  
- btpflash_2(9):  Phase data index 9
"""

import os
import re
import matplotlib.pyplot as plt
import argparse
from typing import Dict, List, Optional, Tuple

# Configuration
DEFAULT_RUN_FILE = os.path.join("Finals_runs", "MEA_MEA_V2", "run.txt")
OUTPUT_DIR = os.path.join("analysis", "results", "VLLE_plots")

# Variables to extract for each stage
BTPFLASH_INDICES = [25, 17, 9]
VARIABLE_LABELS = {
    25: "2nd Liquid Phase",
    17: "1st Liquid Phase", 
    9: "Vapour Phase"
}


def extract_stage_data(file_path: str) -> Dict[int, Dict[int, Optional[float]]]:
    """
    Extract btpflash_2 data for all stages.
    
    Returns:
        Dict[stage_number, Dict[btpflash_index, value]]
    """
    stage_data = {}
    
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return stage_data
    
    # Create patterns for each btpflash index
    patterns = {}
    for idx in BTPFLASH_INDICES:
        patterns[idx] = re.compile(
            r"^\s*Plant\.Absorber\.Stage\((\d+)\)\.btpflash_2\(" + str(idx) + r"\)\s*:\s*([+-]?[0-9.eE+ -]+)"
        )
    
    print(f"Reading from: {file_path}")
    
    with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
        line_count = 0
        for line in fh:
            line_count += 1
            if line_count % 10000 == 0:
                print(f"  Processed {line_count} lines...")
            
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            for idx, pattern in patterns.items():
                match = pattern.match(line)
                if match:
                    stage_num = int(match.group(1))
                    value_str = match.group(2).strip().replace(" ", "")
                    
                    try:
                        value = float(value_str)
                        if stage_num not in stage_data:
                            stage_data[stage_num] = {}
                        stage_data[stage_num][idx] = value
                        
                    except ValueError:
                        print(f"Warning: Could not parse value '{value_str}' for Stage({stage_num}).btpflash_2({idx})")
    
    print(f"Extraction complete. Found data for {len(stage_data)} stages.")
    return stage_data


def create_plots(stage_data: Dict[int, Dict[int, Optional[float]]], output_dir: str) -> List[str]:
    """
    Create plots for the btpflash_2 data.
    
    Returns:
        List of output file paths created
    """
    os.makedirs(output_dir, exist_ok=True)
    output_files = []
    
    if not stage_data:
        print("No data to plot.")
        return output_files
    
    # Prepare data for plotting
    stages = sorted(stage_data.keys())
    
    # Extract data for each btpflash index
    plot_data = {}
    for idx in BTPFLASH_INDICES:
        values = []
        valid_stages = []
        
        for stage in stages:
            if idx in stage_data[stage] and stage_data[stage][idx] is not None:
                values.append(stage_data[stage][idx])
                valid_stages.append(stage)
        
        if values:
            plot_data[idx] = (valid_stages, values)
    
    if not plot_data:
        print("No valid data found for plotting.")
        return output_files
    
    # Create individual plots for each variable
    for idx in BTPFLASH_INDICES:
        if idx not in plot_data:
            continue
            
        valid_stages, values = plot_data[idx]
        
        plt.figure(figsize=(10, 6))
        plt.plot(valid_stages, values, 'o-', linewidth=2, markersize=6, label=VARIABLE_LABELS[idx])
        plt.xlabel('Stage Number')
        plt.ylabel('Phase Fraction')
        plt.title(f'{VARIABLE_LABELS[idx]} Distribution Across Absorber Stages')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.ylim(0, 1.1)
        
        # Add value labels on points for better readability
        for stage, val in zip(valid_stages, values):
            plt.annotate(f'{val:.3e}', (stage, val), 
                        textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)
        
        plt.tight_layout()
        
        phase_name = VARIABLE_LABELS[idx].lower().replace(' ', '_').replace('st', 'st').replace('nd', 'nd')
        output_file = os.path.join(output_dir, f"{phase_name}_vs_stage.png")
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        output_files.append(output_file)
        print(f"Saved: {output_file}")
    
    # Create combined plot with phases and sum on same axes
    plt.figure(figsize=(12, 8))
    
    colors = {'9': 'blue', '17': 'red', '25': 'green'}
    markers = {'9': 'o', '17': 's', '25': '^'}
    
    # Plot individual phases
    all_stages_with_data = set()
    for idx in BTPFLASH_INDICES:
        if idx in plot_data:
            valid_stages, values = plot_data[idx]
            all_stages_with_data.update(valid_stages)
            plt.plot(valid_stages, values, 
                    color=colors[str(idx)], 
                    marker=markers[str(idx)], 
                    linewidth=2, markersize=6, 
                    label=VARIABLE_LABELS[idx])
    
    # Calculate and plot sum to verify it equals 1
    sum_stages = []
    sum_values = []
    
    for stage in sorted(all_stages_with_data):
        stage_sum = 0.0
        has_all_phases = True
        
        for idx in BTPFLASH_INDICES:
            if idx in plot_data:
                stage_values = dict(zip(*plot_data[idx]))
                if stage in stage_values:
                    stage_sum += stage_values[stage]
                else:
                    has_all_phases = False
                    break
            else:
                has_all_phases = False
                break
        
        if has_all_phases:
            sum_stages.append(stage)
            sum_values.append(stage_sum)
    
    # Plot sum of phases
    if sum_stages:
        plt.plot(sum_stages, sum_values, 'ko-', linewidth=3, markersize=8, 
                label='Sum of All Phases', alpha=0.8)
        
        # Add horizontal line at 1.0 for reference
        plt.axhline(y=1.0, color='red', linestyle='--', linewidth=2, 
                   label='Expected Sum = 1.0', alpha=0.7)
        
        # Add annotations showing deviation from 1.0 for significant deviations
        for stage, sum_val in zip(sum_stages, sum_values):
            deviation = abs(sum_val - 1.0)
            if deviation > 0.001:  # Only annotate if significant deviation
                plt.annotate(f'Δ={deviation:.3f}', (stage, sum_val), 
                           textcoords="offset points", xytext=(0,10), 
                           ha='center', fontsize=8, color='red')
    
    # Check if second liquid phase is present (btpflash_2(25) > 0 for any stage)
    second_liquid_present = False
    if 25 in plot_data:
        _, values_25 = plot_data[25]
        second_liquid_present = any(val > 0 for val in values_25)
    
    # Add text annotation about second liquid phase
    phase_status_text = "Second liquid phase present" if second_liquid_present else "No second liquid phase"
    plt.text(0.02, 0.98, phase_status_text, transform=plt.gca().transAxes, 
             fontsize=12, fontweight='bold', 
             bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.8),
             verticalalignment='top')
    
    plt.xlabel('Stage Number')
    plt.ylabel('Phase Fraction')
    plt.title('VLLE Phase Distribution and Balance Check Across Absorber Stages')
    plt.grid(True, alpha=0.0001)
    plt.legend()
    plt.ylim(0, 1.1)
    
    plt.tight_layout()
    
    combined_output = os.path.join(output_dir, "VLLE_phase_analysis.png")
    plt.savefig(combined_output, dpi=150, bbox_inches='tight')
    plt.close()
    output_files.append(combined_output)
    print(f"Saved: {combined_output}")
    
    # Print sum statistics
    if sum_values:
        avg_sum = sum(sum_values) / len(sum_values)
        max_deviation = max(abs(s - 1.0) for s in sum_values)
        print(f"Phase balance statistics:")
        print(f"  Average sum: {avg_sum:.6f}")
        print(f"  Max deviation from 1.0: {max_deviation:.6f}")
        print(f"  Stages with complete data: {len(sum_stages)}")
    else:
        print("Warning: No stages found with complete phase data for sum calculation")
    
    return output_files


def print_summary(stage_data: Dict[int, Dict[int, Optional[float]]]):
    """Print a summary of the extracted data."""
    if not stage_data:
        print("No data extracted.")
        return
    
    print(f"\nData Summary:")
    print(f"Stages found: {min(stage_data.keys())} to {max(stage_data.keys())} ({len(stage_data)} total)")
    
    for idx in BTPFLASH_INDICES:
        count = sum(1 for stage_dict in stage_data.values() 
                   if idx in stage_dict and stage_dict[idx] is not None)
        print(f"btpflash_2({idx}): {count} stages with data")
    
    # Show first few stages as example
    print(f"\nSample data (first 5 stages):")
    sample_stages = sorted(stage_data.keys())[:5]
    
    for stage in sample_stages:
        stage_dict = stage_data[stage]
        values = []
        for idx in BTPFLASH_INDICES:
            val = stage_dict.get(idx)
            if val is not None:
                values.append(f"btpflash_2({idx})={val:.6e}")
            else:
                values.append(f"btpflash_2({idx})=MISSING")
        print(f"  Stage({stage}): {', '.join(values)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_file", nargs="?", default=DEFAULT_RUN_FILE,
                       help="Path to the gSTORE run file")
    parser.add_argument("--output-dir", default=OUTPUT_DIR,
                       help="Output directory for plots")
    parser.add_argument("--no-plot", action="store_true", 
                       help="Extract data but skip plotting")
    args = parser.parse_args()
    
    print("VLLE Plotter - btpflash_2 Analysis")
    print("=" * 50)
    
    # Extract data
    stage_data = extract_stage_data(args.run_file)
    
    # Print summary
    print_summary(stage_data)
    
    # Create plots
    if not args.no_plot and stage_data:
        print(f"\nGenerating plots in: {args.output_dir}")
        output_files = create_plots(stage_data, args.output_dir)
        
        if output_files:
            print(f"\nGenerated {len(output_files)} plot files:")
            for f in output_files:
                print(f"  {f}")
        else:
            print("No plots generated - insufficient data.")
    elif args.no_plot:
        print("Skipping plot generation (--no-plot specified)")


if __name__ == "__main__":
    main()
