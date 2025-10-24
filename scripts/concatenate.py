import os
import sys
from datetime import datetime

def load_variable_order(order_file="good_order.txt"):
    """Load the exact order of variables from good_order.txt"""
    order_list = []
    try:
        with open(order_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('!'):
                    continue
                # Remove leading tab and extract path name before first ':'
                if line.startswith('\t'):
                    line = line[1:]
                if ' : ' in line:
                    path = line.split(' : ')[0]
                    order_list.append(path)
    except FileNotFoundError:
        pass
    return order_list

def format_scientific_notation(value_str):
    """Convert a numeric string to scientific notation format"""
    try:
        # Try to convert to float and format in scientific notation
        num = float(value_str)
        # Format with 17 significant digits (matching original format)
        if num == 0.0:
            return "0.0000000000000000e+00"
        else:
            return f"{num:.16e}"
    except (ValueError, TypeError):
        # If conversion fails, return original string
        return value_str

def read_csv_files(folder_path):
    """
    Read all variables.csv files in a folder structure and return organized data
    
    Args:
        folder_path (str): Path to the folder containing organized CSV files
        
    Returns:
        list: List of dictionaries containing variable data
    """
    all_variables = []
    
    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file == "variables.csv":
                file_path = os.path.join(root, file)
                
                # Get the relative path from the base folder to reconstruct the hierarchy
                relative_path = os.path.relpath(root, folder_path)
                
                # Convert Windows path separators to dots for path name
                if relative_path == ".":
                    path_prefix = ""
                else:
                    path_prefix = relative_path.replace(os.sep, ".") + "."
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as csvfile:
                        for line_num, line in enumerate(csvfile, 1):
                            line = line.strip()
                            if not line:
                                continue
                            
                            # Split the CSV line
                            parts = line.split(',')
                            
                            if len(parts) >= 6:
                                # Full format: variable,value,lower,upper,type,units
                                variable_name = parts[0].strip()
                                value = parts[1].strip()
                                lower_bound = parts[2].strip()
                                upper_bound = parts[3].strip()
                                data_type = parts[4].strip()
                                units = parts[5].strip()
                            elif len(parts) >= 2:
                                # Minimal format: variable,value
                                variable_name = parts[0].strip()
                                value = parts[1].strip()
                                lower_bound = "-1.00000e+20"
                                upper_bound = "1.00000e+20"
                                data_type = "Notype"
                                units = ""
                            else:
                                print(f"Warning: Invalid line format in {file_path} line {line_num}: {line}")
                                continue
                            
                            # Construct full path name
                            full_path = path_prefix + variable_name
                            
                            all_variables.append({
                                'path': full_path,
                                'value': value,
                                'lower_bound': lower_bound,
                                'upper_bound': upper_bound,
                                'type': data_type,
                                'units': units,
                                'source_file': file_path
                            })
                
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return all_variables

def write_txt_file(variables_data, output_file):
    """
    Write variables data to a .txt file in the original format
    
    Args:
        variables_data (list): List of variable dictionaries
        output_file (str): Output file path
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")
        
        with open(output_file, 'w', encoding='utf-8') as txtfile:
            # Write header
            txtfile.write(f"#!gSTORE-4 created on {datetime.now().strftime('%a %b %d %H:%M:%S %Y')}\n")
            txtfile.write("# PROCESS reconstructed_process\n\n")
            txtfile.write("!Time\n\t0\n\n")
            txtfile.write(f"# The total number of variables in the process\n")
            txtfile.write(f"# {len(variables_data)}\n")
            txtfile.write("# Note: all variables are saved\n")
            txtfile.write("!Variables\n")
            txtfile.write("\t# PathName : Value : LowerBound : UpperBound : Type : Units\n")
            
            # Load order from good_order.txt and sort accordingly
            order_list = load_variable_order()
            
            if order_list:
                # Create a mapping of path to its position in the order
                order_map = {path: i for i, path in enumerate(order_list)}
                
                def sort_key(var):
                    path = var['path']
                    if path in order_map:
                        return (0, order_map[path])  # Known variables first, in order
                    else:
                        return (1, path)  # Unknown variables after, alphabetically
                
                sorted_variables = sorted(variables_data, key=sort_key)
            else:
                # Fallback to hierarchy-based sorting if no order file
                def sort_key(var):
                    path = var['path']
                    parts = path.split('.')
                    return (len(parts), tuple(parts))
                
                sorted_variables = sorted(variables_data, key=sort_key)
            
            # Write variable data
            for var in sorted_variables:
                # Format numbers in scientific notation
                value_sci = format_scientific_notation(var['value'])
                lower_sci = format_scientific_notation(var['lower_bound'])
                upper_sci = format_scientific_notation(var['upper_bound'])
                
                # Build the line with proper formatting - no trailing space when units is empty
                if var['units'].strip():
                    line = f"\t{var['path']} : {value_sci} : {lower_sci} : {upper_sci} : {var['type']} : {var['units']}\n"
                else:
                    line = f"\t{var['path']} : {value_sci} : {lower_sci} : {upper_sci} : {var['type']} :\n"
                txtfile.write(line)
        
        print(f"Successfully wrote {len(variables_data)} variables to {output_file}")
        
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")

def get_user_input():
    """Get input folder path and output file name from user"""
    print("=== CSV to TXT Concatenator ===")
    print()
    
    # Get run name and construct paths
    while True:
        run_name = input("Enter run name (e.g., run1, run2) or press Enter for 'run1': ").strip()
        if not run_name:
            run_name = "run1"
        
        # Construct input folder path
        folder_path = f"Trials/{run_name}/organized_output"
        
        # Check if folder exists
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            break
        else:
            print(f"Error: Folder '{folder_path}' not found. Please try again.")
    
    # Automatically construct output file path
    output_file = f"Corrections/{run_name}/reconstructed.txt"

    # Ensure .txt extension
    if not output_file.endswith('.txt'):
        output_file += '.txt'
    
    return folder_path, output_file

def main():
    """
    Main execution function - concatenate CSV files back to .txt format
    """
    
    # Check if folder path provided as command line argument
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "reconstructed.txt"
        
        # Check if folder exists
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            print(f"Error: Folder '{folder_path}' not found.")
            return
        
        # Ensure .txt extension
        if not output_file.endswith('.txt'):
            output_file += '.txt'
    else:
        # Get user input interactively
        folder_path, output_file = get_user_input()
    
    print()
    print(f"Reading CSV files from: {folder_path}")
    print(f"Output file: {output_file}")
    print()
    
    # Read all CSV files
    print("Scanning for CSV files...")
    variables_data = read_csv_files(folder_path)
    
    if not variables_data:
        print("No variables found in CSV files.")
        return
    
    print(f"Found {len(variables_data)} variables from CSV files")
    
    # Write to TXT file
    print("Writing to TXT file...")
    write_txt_file(variables_data, output_file)
    
    print("Process completed successfully!")

def show_usage():
    """Show usage information"""
    print("Usage:")
    print("  python concatenate.py [folder_path] [output_file]")
    print()
    print("Arguments:")
    print("  folder_path   Path to folder containing organized CSV files (default: organized_output)")
    print("  output_file   Output .txt file name (default: reconstructed.txt)")
    print()
    print("Examples:")
    print("  python concatenate.py                                    # Interactive mode")
    print("  python concatenate.py organized_output                   # Use organized_output folder")
    print("  python concatenate.py organized_output my_data.txt       # Custom output name")

if __name__ == "__main__":
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', '/?']:
        show_usage()
    else:
        main()