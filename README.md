# gPROMS Process Simulation Data Processing

A Python toolkit for processing and analyzing gSTORE-4 format files from gPROMS chemical process simulations, specifically designed for carbon capture plant optimization studies using MEA/DEEA solvent systems.

## Overview

This project provides a complete data processing pipeline for gPROMS simulation results, handling thousands of process variables from complex chemical plant models. The system converts hierarchical simulation data between gSTORE-4 text format and organized CSV structures for analysis and reconstruction.

## Features

- **Parse gSTORE-4 Files**: Convert complex simulation output files into organized CSV hierarchies
- **Hierarchical Data Organization**: Automatically organize variables by equipment hierarchy (Plant → Absorber → Stage(n))
- **Data Reconstruction**: Rebuild gSTORE-4 files from CSV data with preserved precision
- **Interactive & Batch Processing**: Support for both interactive selection and command-line batch operations
- **Scientific Notation Preservation**: Maintain 16-digit precision for engineering calculations
- **Multiple Processing Scripts**: Choose between different reconstruction algorithms

## Project Structure

```
├── scripts/                    # Main processing scripts
│   ├── analyse.py             # Core parsing and organization functions
│   ├── app.py                 # Interactive data organization interface
│   ├── concatenate.py         # CSV to gSTORE-4 reconstruction (v1)
│   └── concatenateV2.py       # Improved reconstruction with deterministic ordering
├── Trials/                    # Input simulation data
│   └── {run_name}/
│       ├── run_*.txt          # Raw gSTORE-4 simulation files
│       └── organized_output/  # Hierarchical CSV structure
├── Corrections/               # Reconstructed output files
│   └── {run_name}/
│       └── reconstructed.txt  # Rebuilt gSTORE-4 files
└── venv/                     # Python virtual environment
```

## Data Organization

The processing pipeline creates a hierarchical data structure that mirrors the chemical plant equipment layout:

```
Trials/{run_name}/
├── run_{n}.txt                    # Raw gSTORE-4 input
└── organized_output/              # Hierarchical CSV output
    └── Plant/
        ├── variables.csv          # Plant-level variables
        ├── Absorber/
        │   ├── variables.csv      # Absorber variables
        │   └── Stage(1)/...       # Individual stages
        └── Holdup_tank/...

Corrections/{run_name}/
└── reconstructed.txt              # Rebuilt gSTORE-4 file
```

This organization allows for:
- **Equipment-based analysis**: Each folder represents a plant component
- **Hierarchical data access**: Variables are grouped by their physical location in the plant
- **Scalable processing**: Individual CSV files can be processed independently
- **Data traceability**: Clear mapping between simulation paths and file locations

## Installation

1. **Clone the repository** or download the project files
2. **Create a virtual environment** (recommended):
   ```powershell
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```
3. **Install dependencies** (if any additional packages are needed):
   ```powershell
   pip install -r requirements.txt  # If requirements file exists
   ```

## Usage

### 1. Parse Simulation Data

Convert a gSTORE-4 file to organized CSV structure:

```powershell
cd scripts
python app.py
```

**Interactive mode:**
- Enter input file path (e.g., `Trials/run1/run_1.txt`)
- Specify output directory (auto-generated as `Trials/{run}/organized_output`)
- Script creates hierarchical folder structure with `variables.csv` files

### 2. Reconstruct gSTORE-4 Files

Convert organized CSV data back to gSTORE-4 format:

```powershell
# Using improved v2 algorithm (recommended)
python concatenateV2.py

# Using original algorithm
python concatenate.py
```

**Command-line mode:**
```powershell
python concatenateV2.py run1  # Process specific run
```

### 3. Analyze Specific Variables

Use the analysis functions for targeted data extraction:

```python
from analyse import read_matching_values_from_txt, organize_specific_path

# Read all absorber variables
absorber_data = read_matching_values_from_txt("Trials/run1/run_1.txt", "Plant.Absorber")

# Organize only specific equipment data
organize_specific_path("Trials/run1/run_1.txt", "Plant.Absorber", "absorber_analysis")
```

## Data Format

### Input: gSTORE-4 Format
```
PathName : Value : LowerBound : UpperBound : Type : Units
Plant.Absorber.Stage(1).temperature : 3.5000e+02 : 2.5000e+02 : 4.5000e+02 : Temperature : K
```

### Output: CSV Format
```
temperature,3.5000e+02,2.5000e+02,4.5000e+02,Temperature,K
```

### Hierarchical Organization
- **Path**: `Plant.Absorber.Stage(1).temperature`
- **Folder**: `organized_output/Plant/Absorber/Stage(1)/`
- **File**: `variables.csv`
- **Variable**: `temperature`

## Key Features Explained

### Scientific Notation Preservation
All numerical values are maintained with 16-digit precision using scientific notation (`f"{num:.16e}"`), essential for engineering calculations and simulation accuracy.

### Hierarchical Path Parsing
Equipment hierarchies like `Plant.Absorber.Stage(1).temperature` are automatically parsed to create folder structures that mirror the physical plant layout.

### Deterministic Processing
Files and directories are processed in sorted order to ensure consistent output across different systems and runs.

### Error Handling
- Validates file existence before processing
- Skips malformed data lines while continuing processing
- Provides detailed feedback on variable counts and file creation

## Common Workflows

### Processing a New Simulation Run
1. Place gSTORE-4 file in `Trials/{run_name}/run_*.txt`
2. Run `python app.py` to parse and organize data
3. Analyze organized CSV files as needed
4. Run `python concatenateV2.py {run_name}` to reconstruct if modifications were made

### Batch Processing Multiple Runs
```powershell
# Process multiple runs sequentially
foreach ($run in @("run1", "run2", "run3")) {
    python concatenateV2.py $run
}
```

### Analyzing Specific Equipment
Focus on particular plant components by using path prefixes:
- `Plant.Absorber` - All absorber variables
- `Plant.Holdup_tank` - Tank-related variables  
- `Plant.Absorber.Stage(1)` - Specific stage data

## Contributing

When modifying or extending the codebase:

1. **Preserve data precision** - always use scientific notation for numerical values
2. **Maintain hierarchy** - respect the equipment path structure 
3. **Handle missing data** - many variables may have empty units or bounds
4. **Test with real data** - use actual simulation files for validation
5. **Follow naming conventions** - use the established `Trials/` and `Corrections/` directory patterns

## Troubleshooting

### Common Issues

**File Not Found Errors:**
- Verify file paths use forward slashes or raw strings
- Check that simulation files are in correct `Trials/{run}/` structure

**Numerical Precision Loss:**
- Always use `format_scientific_notation()` function for number formatting
- Avoid standard float formatting that loses precision

**Memory Issues with Large Files:**
- Process files in chunks if dealing with >50K variables
- Consider using `concatenateV2.py` for improved memory efficiency

**Inconsistent Output Ordering:**
- Use `concatenateV2.py` for deterministic, sorted output
- Ensure directories are processed with `sorted()` function

## License

[Add your license information here]

## Contact

[Add contact information or links to documentation]