#!/usr/bin/env python3
"""
CO2 Equilibrium Analysis for gSTORE run files.

Plots CO2 partial pressure vs CO2 loading for each stage in the absorber.
Calculates: Plant.Absorber.Stage(i).trans_prop.stg_pressure * Plant.Absorber.Stage(i).trans_prop.mole_frac_vap("CO2")
vs Plant.Absorber.Stage(i).trans_prop.loading_CO2

This represents the CO2 equilibrium relationship in the absorber column.
"""

import os
import re
import matplotlib.pyplot as plt
import numpy as np
import argparse
from typing import Dict, List, Optional, Tuple

# Configure matplotlib for LaTeX rendering
plt.rcParams['text.usetex'] = False  # Set to True if you have LaTeX installed
plt.rcParams['mathtext.default'] = 'regular'
plt.rcParams['font.size'] = 11

# Configuration
DEFAULT_RUN_FILE = os.path.join("Finals_runs", "MEA", "run.txt")
OUTPUT_DIR = os.path.join("analysis", "results", "plots")

# Variables to extract for each stage
REQUIRED_VARIABLES = {
    "pressure": r"Plant\.Absorber\.Stage\((\d+)\)\.trans_prop\.stg_pressure\s*:\s*([+-]?[0-9.eE+ -]+)",
    "co2_mole_frac": r"Plant\.Absorber\.Stage\((\d+)\)\.trans_prop\.mole_frac_vap\(\"CO2\"\)\s*:\s*([+-]?[0-9.eE+ -]+)",
    "loading_co2": r"Plant\.Absorber\.Stage\((\d+)\)\.trans_prop\.loading_CO2\s*:\s*([+-]?[0-9.eE+ -]+)"
}


def extract_stage_data(file_path: str) -> Dict[int, Dict[str, Optional[float]]]:
    """
    Extract CO2 equilibrium data for all stages.
    
    Returns:
        Dict[stage_number, Dict[variable_name, value]]
    """
    stage_data = {}
    
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return stage_data
    
    # Compile patterns for each variable
    patterns = {}
    for var_name, pattern_str in REQUIRED_VARIABLES.items():
        patterns[var_name] = re.compile(pattern_str)
    
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
                
            for var_name, pattern in patterns.items():
                match = pattern.match(line)
                if match:
                    stage_num = int(match.group(1))
                    value_str = match.group(2).strip().replace(" ", "")
                    
                    try:
                        value = float(value_str)
                        if stage_num not in stage_data:
                            stage_data[stage_num] = {}
                        stage_data[stage_num][var_name] = value
                        
                    except ValueError:
                        print(f"Warning: Could not parse value '{value_str}' for Stage({stage_num}) {var_name}")
    
    print(f"Extraction complete. Found data for {len(stage_data)} stages.")
    return stage_data


def calculate_partial_pressure(stage_data: Dict[int, Dict[str, Optional[float]]]) -> Dict[int, Dict[str, float]]:
    """
    Calculate CO2 partial pressure and prepare data for plotting.
    
    Returns:
        Dict[stage_number, Dict[metric_name, value]]
    """
    calculated_data = {}
    
    for stage_num, variables in stage_data.items():
        # Check if all required variables are present
        if all(var in variables and variables[var] is not None 
               for var in ["pressure", "co2_mole_frac", "loading_co2"]):
            
            pressure = variables["pressure"]  # Pa
            co2_mole_frac = variables["co2_mole_frac"]  # dimensionless
            loading_co2 = variables["loading_co2"]  # dimensionless
            
            # Calculate CO2 partial pressure (Pa)
            co2_partial_pressure = pressure * co2_mole_frac
            
            calculated_data[stage_num] = {
                "co2_partial_pressure_Pa": co2_partial_pressure,
                "co2_partial_pressure_kPa": co2_partial_pressure / 1000,  # Convert to kPa
                "loading_co2": loading_co2,
                "stage_pressure_Pa": pressure,
                "co2_mole_fraction": co2_mole_frac
            }
    
    return calculated_data


def create_plots(calculated_data: Dict[int, Dict[str, float]], output_dir: str, run_name: str) -> List[str]:
    """
    Create plots for CO2 equilibrium data.
    
    Returns:
        List of output file paths created
    """
    os.makedirs(output_dir, exist_ok=True)
    output_files = []
    
    if not calculated_data:
        print("No data to plot.")
        return output_files
    
    # Prepare data arrays
    stages = sorted(calculated_data.keys())
    co2_partial_pressure_kPa = [calculated_data[stage]["co2_partial_pressure_kPa"] for stage in stages]
    co2_partial_pressure_Pa = [calculated_data[stage]["co2_partial_pressure_Pa"] for stage in stages]
    loading_co2 = [calculated_data[stage]["loading_co2"] for stage in stages]
    co2_mole_fraction = [calculated_data[stage]["co2_mole_fraction"] for stage in stages]
    stage_pressure_Pa = [calculated_data[stage]["stage_pressure_Pa"] for stage in stages]
    
    # Plot 1: CO2 Partial Pressure vs CO2 Loading (Main Equilibrium Plot)
    plt.figure(figsize=(10, 8))
    
    # Create scatter plot with stage numbers as labels
    scatter = plt.scatter(loading_co2, co2_partial_pressure_kPa, 
                         c=stages, cmap='viridis', s=80, alpha=0.7, edgecolors='black')
    
    # Add stage number labels to each point
    for i, stage in enumerate(stages):
        plt.annotate(f'{stage}', (loading_co2[i], co2_partial_pressure_kPa[i]), 
                    xytext=(5, 5), textcoords='offset points', 
                    fontsize=8, alpha=0.8)
    
    # Add colorbar to show stage progression
    cbar = plt.colorbar(scatter)
    cbar.set_label('Stage Number', rotation=270, labelpad=15)
    
    plt.xlabel(r'$\alpha_{CO_2}$ (mol $CO_2$/mol absorbent)', fontsize=12)
    plt.ylabel(r'$P_{CO_2}$ (kPa)', fontsize=12)
    plt.title(rf'$CO_2$ Equilibrium: Partial Pressure vs Loading ({run_name})', fontsize=14)
    plt.grid(True, alpha=0.0003)
    
    # Add trend lines
    if len(loading_co2) > 1:
        # Linear trend with R²
        z_linear = np.polyfit(loading_co2, co2_partial_pressure_kPa, 1)
        p_linear = np.poly1d(z_linear)
        x_trend = np.linspace(min(loading_co2), max(loading_co2), 100)
        y_linear_pred = p_linear(loading_co2)
        
        # Calculate R² for linear fit
        ss_res_linear = np.sum((co2_partial_pressure_kPa - y_linear_pred) ** 2)
        ss_tot_linear = np.sum((co2_partial_pressure_kPa - np.mean(co2_partial_pressure_kPa)) ** 2)
        r2_linear = 1 - (ss_res_linear / ss_tot_linear) if ss_tot_linear > 0 else 0
        
        #plt.plot(x_trend, p_linear(x_trend), "r--", alpha=0.8, linewidth=2, 
                #label=f'Linear: P_CO₂ = {z_linear[0]:.2f}×Loading + {z_linear[1]:.2f} (R²={r2_linear:.3f})')
        
        # Power law trend (y = a * x^b)
        # Filter positive loading values for power law fitting
        positive_indices = [i for i, load in enumerate(loading_co2) if load > 0]
        if len(positive_indices) > 1:
            loading_pos = [loading_co2[i] for i in positive_indices]
            pressure_pos = [co2_partial_pressure_kPa[i] for i in positive_indices]
            
            # Fit power law function: P_CO2 = a * Loading^b
            # Take log of both sides: log(P_CO2) = log(a) + b*log(Loading)
            log_loading = np.log(loading_pos)
            log_pressure = np.log(pressure_pos)
            z_power = np.polyfit(log_loading, log_pressure, 1)
            
            # Extract power law parameters: a = exp(intercept), b = slope
            a_power = np.exp(z_power[1])
            b_power = z_power[0]
            
            # Generate smooth curve for power law trend
            x_power_trend = np.linspace(min(loading_pos), max(loading_pos), 100)
            y_power_trend = a_power * (x_power_trend ** b_power)
            
            # Calculate R² for power law fit
            y_power_pred = a_power * (np.array(loading_pos) ** b_power)
            ss_res_power = np.sum((pressure_pos - y_power_pred) ** 2)
            ss_tot_power = np.sum((pressure_pos - np.mean(pressure_pos)) ** 2)
            r2_power = 1 - (ss_res_power / ss_tot_power) if ss_tot_power > 0 else 0
            
            plt.plot(x_power_trend, y_power_trend, "g--", alpha=0.8, linewidth=2,
                    label=rf'Power law: $P_{{CO_2}} = {a_power:.2f} \times \alpha_{{CO_2}}^{{{b_power:.2f}}}$ ($R^2={r2_power:.3f}$)')
        
        plt.legend()
    
    plt.tight_layout()
    
    output_file = os.path.join(output_dir, f"co2_equilibrium_{run_name}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    output_files.append(output_file)
    print(f"Saved: {output_file}")
    
    # Plot 2: Stage-by-stage progression
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # CO2 Loading by stage
    ax1.plot(stages, loading_co2, 'bo-', linewidth=2, markersize=6)
    ax1.set_xlabel('Stage Number')
    ax1.set_ylabel(r'$\alpha_{CO_2}$ (mol $CO_2$/mol abs.)')
    ax1.set_title(r'$CO_2$ Loading Profile')
    ax1.grid(True, alpha=0.3)
    
    # CO2 Partial Pressure by stage
    ax2.plot(stages, co2_partial_pressure_kPa, 'ro-', linewidth=2, markersize=6)
    ax2.set_xlabel('Stage Number')
    ax2.set_ylabel(r'$P_{CO_2}$ (kPa)')
    ax2.set_title(r'$CO_2$ Partial Pressure Profile')
    ax2.grid(True, alpha=0.3)
    
    # CO2 Mole Fraction by stage
    ax3.plot(stages, co2_mole_fraction, 'go-', linewidth=2, markersize=6)
    ax3.set_xlabel('Stage Number')
    ax3.set_ylabel(r'$y_{CO_2}$ (vapor mole fraction)')
    ax3.set_title(r'$CO_2$ Mole Fraction Profile')
    ax3.grid(True, alpha=0.3)
    
    # Stage Pressure by stage
    ax4.plot(stages, [p/1000 for p in stage_pressure_Pa], 'mo-', linewidth=2, markersize=6)
    ax4.set_xlabel('Stage Number')
    ax4.set_ylabel(r'$P_{stage}$ (kPa)')
    ax4.set_title('Stage Pressure Profile')
    ax4.grid(True, alpha=0.3)
    
    plt.suptitle(rf'$CO_2$ Process Variables by Stage ({run_name})', fontsize=16)
    plt.tight_layout()
    
    output_file = os.path.join(output_dir, f"co2_stage_profiles_{run_name}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    output_files.append(output_file)
    print(f"Saved: {output_file}")
    
    # Plot 3: Log-scale equilibrium plot (useful for Henry's law analysis)
    plt.figure(figsize=(10, 8))
    
    # Filter out zero or negative values for log plot
    valid_indices = [i for i, (loading, pressure) in enumerate(zip(loading_co2, co2_partial_pressure_kPa)) 
                     if loading > 0 and pressure > 0]
    
    if valid_indices:
        valid_loading = [loading_co2[i] for i in valid_indices]
        valid_pressure = [co2_partial_pressure_kPa[i] for i in valid_indices]
        valid_stages = [stages[i] for i in valid_indices]
        
        scatter = plt.scatter(valid_loading, valid_pressure, 
                             c=valid_stages, cmap='viridis', s=80, alpha=0.7, edgecolors='black')
        
        # Add stage number labels
        for i, stage in enumerate(valid_stages):
            plt.annotate(f'{stage}', (valid_loading[i], valid_pressure[i]), 
                        xytext=(5, 5), textcoords='offset points', 
                        fontsize=8, alpha=0.8)
        
        plt.colorbar(scatter, label='Stage Number')
        
        plt.xscale('log')
        plt.yscale('log')
        plt.xlabel(r'$\alpha_{CO_2}$ (mol $CO_2$/mol absorbent) [log scale]', fontsize=12)
        plt.ylabel(r'$P_{CO_2}$ (kPa) [log scale]', fontsize=12)
        plt.title(rf'$CO_2$ Equilibrium: Log-Log Plot ({run_name})', fontsize=14)
        plt.grid(True, alpha=0.3)
        
        # Add Henry's law reference line (linear in log-log plot)
        if len(valid_loading) > 1:
            log_loading = np.log10(valid_loading)
            log_pressure = np.log10(valid_pressure)
            z = np.polyfit(log_loading, log_pressure, 1)
            
            x_range = np.logspace(np.log10(min(valid_loading)), np.log10(max(valid_loading)), 100)
            y_henry = 10**(z[0] * np.log10(x_range) + z[1])
            plt.plot(x_range, y_henry, "r--", alpha=0.8, linewidth=2, 
                    label=rf'Power law fit: $P \propto \alpha_{{CO_2}}^{{{z[0]:.2f}}}$')
            plt.legend()
    
    plt.tight_layout()
    
    output_file = os.path.join(output_dir, f"co2_equilibrium_loglog_{run_name}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    output_files.append(output_file)
    print(f"Saved: {output_file}")
    
    return output_files


def export_data_csv(calculated_data: Dict[int, Dict[str, float]], output_dir: str, run_name: str) -> str:
    """Export the calculated data to CSV format."""
    import csv
    
    os.makedirs(output_dir, exist_ok=True)
    csv_file = os.path.join(output_dir, f"co2_equilibrium_data_{run_name}.csv")
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'Stage',
            'CO2_Loading_mol_per_mol',
            'CO2_Partial_Pressure_Pa',
            'CO2_Partial_Pressure_kPa', 
            'CO2_Mole_Fraction_Vapor',
            'Stage_Pressure_Pa'
        ])
        
        # Data rows
        for stage in sorted(calculated_data.keys()):
            data = calculated_data[stage]
            writer.writerow([
                stage,
                f"{data['loading_co2']:.6e}",
                f"{data['co2_partial_pressure_Pa']:.6e}",
                f"{data['co2_partial_pressure_kPa']:.6e}",
                f"{data['co2_mole_fraction']:.6e}",
                f"{data['stage_pressure_Pa']:.6e}"
            ])
    
    print(f"Exported data to: {csv_file}")
    return csv_file


def print_summary(stage_data: Dict[int, Dict[str, Optional[float]]], 
                 calculated_data: Dict[int, Dict[str, float]]):
    """Print a summary of the extracted and calculated data."""
    if not stage_data:
        print("No data extracted.")
        return
    
    print(f"\nData Summary:")
    print(f"Stages found: {min(stage_data.keys())} to {max(stage_data.keys())} ({len(stage_data)} total)")
    print(f"Stages with complete data: {len(calculated_data)}")
    
    # Count available data for each variable
    for var_name in REQUIRED_VARIABLES.keys():
        count = sum(1 for stage_dict in stage_data.values() 
                   if var_name in stage_dict and stage_dict[var_name] is not None)
        print(f"{var_name}: {count} stages with data")
    
    if calculated_data:
        stages = sorted(calculated_data.keys())
        
        # Statistics
        loadings = [calculated_data[s]["loading_co2"] for s in stages]
        pressures_kPa = [calculated_data[s]["co2_partial_pressure_kPa"] for s in stages]
        
        print(f"\nCO₂ Loading Statistics:")
        print(f"  Range: {min(loadings):.4f} to {max(loadings):.4f}")
        print(f"  Average: {np.mean(loadings):.4f}")
        
        print(f"\nCO₂ Partial Pressure Statistics (kPa):")
        print(f"  Range: {min(pressures_kPa):.4f} to {max(pressures_kPa):.4f}")
        print(f"  Average: {np.mean(pressures_kPa):.4f}")
        
        # Show sample data
        print(f"\nSample data (first 5 stages with complete data):")
        sample_stages = stages[:5]
        
        for stage in sample_stages:
            data = calculated_data[stage]
            print(f"  Stage({stage}): Loading={data['loading_co2']:.4f}, "
                  f"P_CO2={data['co2_partial_pressure_kPa']:.2f} kPa, "
                  f"y_CO2={data['co2_mole_fraction']:.4f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_file", nargs="?", default=DEFAULT_RUN_FILE,
                       help="Path to the gSTORE run file")
    parser.add_argument("--output-dir", default=OUTPUT_DIR,
                       help="Output directory for plots and data")
    parser.add_argument("--no-plot", action="store_true", 
                       help="Extract data but skip plotting")
    parser.add_argument("--export-csv", action="store_true",
                       help="Export calculated data to CSV")
    args = parser.parse_args()
    
    print("CO₂ Equilibrium Analysis")
    print("=" * 50)
    
    # Determine run name from file path
    run_name = os.path.basename(os.path.dirname(args.run_file))
    if not run_name:
        run_name = "unknown_run"
    
    # Extract data
    stage_data = extract_stage_data(args.run_file)
    
    # Calculate CO2 partial pressure and other metrics
    calculated_data = calculate_partial_pressure(stage_data)
    
    # Print summary
    print_summary(stage_data, calculated_data)
    
    # Export to CSV if requested
    if args.export_csv and calculated_data:
        csv_file = export_data_csv(calculated_data, args.output_dir, run_name)
    
    # Create plots
    if not args.no_plot and calculated_data:
        print(f"\nGenerating plots in: {args.output_dir}")
        output_files = create_plots(calculated_data, args.output_dir, run_name)
        
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