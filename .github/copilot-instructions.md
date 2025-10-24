# gPROMS Process Simulation Data Processing

## Project Overview

This is a **gPROMS process simulation data processing pipeline** for chemical plant optimization. The system processes gSTORE-4 format files containing thousands of process variables from carbon capture plant simulations (MEA/DEEA solvents).

## Core Architecture & Data Flow

### 1. Input Data Format (gSTORE-4)
- **Files**: `Trials/{run_name}/run_*.txt` (16K+ variables each)
- **Format**: `PathName : Value : LowerBound : UpperBound : Type : Units`
- **Structure**: Hierarchical dot-notation paths like `Plant.Absorber.Stage(1).temperature`
- **Example**: `Plant.Hold_up : 3.1929454457913710e-02 : -1.00000e+20 : 1.00000e+20 : notype :`

### 2. Processing Pipeline
1. **Parse** (`analyse.py`): Convert txt → hierarchical CSV structure
2. **Organize** (`app.py`): Interactive interface for data organization  
3. **Reconstruct** (`concatenate.py`/`concatenateV2.py`): CSV → txt with scientific notation

### 3. Directory Structure Convention
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

## Key Implementation Patterns

### Path Parsing & CSV Organization
- **Dot notation splitting**: `path.split('.')` creates folder hierarchy
- **Variable extraction**: Last path component becomes CSV variable name
- **CSV format**: `variable,value,lower,upper,type,units` (no headers)

### Scientific Notation Handling
```python
# Always format numbers to 16-digit scientific notation
f"{num:.16e}"  # Maintains precision for engineering calculations
```

### File Processing Workflow
- **Parse once, organize by hierarchy**: Each `variables.csv` contains related process variables
- **Deterministic ordering**: Use `os.walk()` with sorted directories for consistent output
- **Batch processing**: Process all runs with same script via command-line or interactive mode

## Essential Functions

- `organize_values_to_folders()`: Core parser - txt to hierarchical CSV
- `read_csv_files()`: Reverse parser - CSV back to variable list
- `format_scientific_notation()`: Maintains engineering precision
- `get_user_input()`: Interactive run selection with path validation

## Development Guidelines

### Working with Process Variables
- **Always preserve scientific notation precision** - these are engineering calculations
- **Respect hierarchical structure** - path organization mirrors plant equipment hierarchy  
- **Handle missing units gracefully** - many variables have empty units field
- **Use relative paths** for run organization (`Trials/{run}/` pattern)

### File Operations
- **Check file existence** before processing (common user error)
- **Create output directories automatically** (`os.makedirs(exist_ok=True)`)
- **Use UTF-8 encoding** for CSV files to handle special characters
- **Sort directories/files** for deterministic output ordering

### Error Handling
- **Validate numeric conversion** - some values may not parse as float
- **Skip malformed lines** but continue processing
- **Provide clear feedback** on file counts and variable counts processed

## Common Tasks

### Adding New Run Processing
```python
# Pattern for run-based file paths
input_file = f"Trials/{run_name}/run_{n}.txt"
output_dir = f"Trials/{run_name}/organized_output"
corrected_file = f"Corrections/{run_name}/reconstructed.txt"
```

### Processing Multiple Runs
Use command-line arguments or interactive prompts following the established pattern in `concatenateV2.py`.

### Extending Variable Analysis
When adding analysis functions, follow the pattern in `analyse.py` - work with dictionaries of `{path: value}` and preserve the full 6-column data structure.