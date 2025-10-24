def read_value_from_txt(file_path, path_name):
    """
    Read a value from a .txt file based on the path name prefix.
    
    Args:
        file_path (str): Path to the .txt file
        path_name (str): The path name prefix to search for
        
    Returns:
        float: The value associated with the first matching path, or None if not found
        
    File format expected:
    PathName : Value : LowerBound : UpperBound : Type : Units
    """
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Split by ':' and clean whitespace
                parts = [part.strip() for part in line.split(':')]
                
                if len(parts) >= 6:  # Ensure we have all expected parts
                    current_path = parts[0]
                    value_str = parts[1]
                    
                    # Check if current path starts with the given prefix
                    if current_path.startswith(path_name):
                        try:
                            # Convert value to float
                            value = float(value_str)
                            print(f"Found matching path: '{current_path}'")
                            return value
                        except ValueError:
                            print(f"Warning: Could not convert value '{value_str}' to float for path '{current_path}'")
                            continue  # Continue searching for other matches
        
        print(f"No paths starting with '{path_name}' found in file '{file_path}'")
        return None
        
    except FileNotFoundError:
        print(f"File '{file_path}' not found")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def read_all_values_from_txt(file_path, path_prefix=None):
    """
    Read all values from a .txt file and return as a dictionary.
    
    Args:
        file_path (str): Path to the .txt file
        path_prefix (str, optional): If provided, only return paths that start with this prefix
        
    Returns:
        dict: Dictionary with path names as keys and values as values
    """
    values_dict = {}
    
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Split by ':' and clean whitespace
                parts = [part.strip() for part in line.split(':')]
                
                if len(parts) >= 6:  # Ensure we have all expected parts
                    path_name = parts[0]
                    value_str = parts[1]
                    
                    # Filter by prefix if provided
                    if path_prefix and not path_name.startswith(path_prefix):
                        continue
                    
                    try:
                        # Convert value to float
                        value = float(value_str)
                        values_dict[path_name] = value
                    except ValueError:
                        print(f"Warning: Could not convert value '{value_str}' to float for path '{path_name}'")
                        continue
        
        return values_dict
        
    except FileNotFoundError:
        print(f"File '{file_path}' not found")
        return {}
    except Exception as e:
        print(f"Error reading file: {e}")
        return {}


def read_matching_values_from_txt(file_path, path_prefix):
    """
    Read all values from a .txt file that match a given path prefix.
    
    Args:
        file_path (str): Path to the .txt file
        path_prefix (str): The path prefix to search for
        
    Returns:
        dict: Dictionary with matching path names as keys and values as values
    """
    return read_all_values_from_txt(file_path, path_prefix)


def organize_values_to_folders(file_path, output_base_dir="output"):
    """
    Read a .txt file and organize values into folders based on PathName structure.
    Creates CSV files with variable names and values.
    
    Args:
        file_path (str): Path to the input .txt file
        output_base_dir (str): Base directory for output folders
        
    Returns:
        dict: Summary of files created
    """
    import os
    import csv
    from collections import defaultdict
    
    # Dictionary to store data by folder path
    folder_data = defaultdict(list)
    
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Split by ':' and clean whitespace
                parts = [part.strip() for part in line.split(':')]
                
                if len(parts) >= 6:  # Ensure we have all expected parts
                    path_name = parts[0]
                    value_str = parts[1]
                    lower_bound = parts[2]
                    upper_bound = parts[3]
                    data_type = parts[4]
                    units = parts[5]
                    
                    try:
                        # Convert value to float
                        value = float(value_str)
                        
                        # Parse the path to determine folder structure
                        path_parts = path_name.split('.')
                        
                        if len(path_parts) >= 2:
                            # Create folder path (all parts except the last one)
                            folder_path = os.path.join(output_base_dir, *path_parts[:-1])
                            
                            # Variable name is the last part
                            variable_name = path_parts[-1]
                            
                            # Store the data (all columns)
                            folder_data[folder_path].append({
                                'Variable': variable_name,
                                'Value': value,
                                'LowerBound': lower_bound,
                                'UpperBound': upper_bound,
                                'Type': data_type,
                                'Units': units
                            })
                        
                    except ValueError:
                        print(f"Warning: Could not convert value '{value_str}' to float for path '{path_name}'")
                        continue
        
        # Create folders and CSV files
        files_created = {}
        
        for folder_path, data_list in folder_data.items():
            # Create the directory if it doesn't exist
            os.makedirs(folder_path, exist_ok=True)
            
            # Create CSV file path
            csv_file_path = os.path.join(folder_path, 'variables.csv')
            
            # Write CSV file (plain lines with all columns)
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Write data with all columns
                for row in data_list:
                    var = str(row['Variable']).replace('\n', ' ')
                    val = row['Value']
                    lower = row['LowerBound']
                    upper = row['UpperBound']
                    dtype = row['Type']
                    units = row['Units']
                    csvfile.write(f"{var},{val},{lower},{upper},{dtype},{units}\n")
            
            files_created[folder_path] = {
                'csv_file': csv_file_path,
                'variable_count': len(data_list)
            }
            
            # Removed verbose print statement for cleaner output
        
        return files_created
        
    except FileNotFoundError:
        print(f"File '{file_path}' not found")
        return {}
    except Exception as e:
        print(f"Error processing file: {e}")
        return {}


def organize_specific_path(file_path, path_prefix, output_base_dir="output"):
    """
    Organize values for a specific path prefix into folders.
    
    Args:
        file_path (str): Path to the input .txt file
        path_prefix (str): Path prefix to filter data
        output_base_dir (str): Base directory for output folders
        
    Returns:
        dict: Summary of files created for the specific prefix
    """
    import os
    import csv
    from collections import defaultdict
    
    # Get matching values
    matching_values = read_matching_values_from_txt(file_path, path_prefix)
    
    if not matching_values:
        print(f"No values found for prefix '{path_prefix}'")
        return {}
    
    # Dictionary to store data by folder path
    folder_data = defaultdict(list)
    
    # Read the file again to get all the additional data (bounds, type, units)
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Split by ':' and clean whitespace
                parts = [part.strip() for part in line.split(':')]
                
                if len(parts) >= 6:  # Ensure we have all expected parts
                    path_name = parts[0]
                    
                    # Check if this path matches our prefix and is in our matching values
                    if path_name in matching_values:
                        value_str = parts[1]
                        lower_bound = parts[2]
                        upper_bound = parts[3]
                        data_type = parts[4]
                        units = parts[5]
                        
                        # Parse the path to determine folder structure
                        path_parts = path_name.split('.')
                        
                        if len(path_parts) >= 2:
                            # Create folder path (all parts except the last one)
                            folder_path = os.path.join(output_base_dir, *path_parts[:-1])
                            
                            # Variable name is the last part
                            variable_name = path_parts[-1]
                            
                            # Store the data (all columns)
                            folder_data[folder_path].append({
                                'Variable': variable_name,
                                'Value': matching_values[path_name],
                                'LowerBound': lower_bound,
                                'UpperBound': upper_bound,
                                'Type': data_type,
                                'Units': units
                            })
        
        # Create folders and CSV files
        files_created = {}
        
        for folder_path, data_list in folder_data.items():
            # Create the directory if it doesn't exist
            os.makedirs(folder_path, exist_ok=True)
            
            # Create CSV file path
            csv_file_path = os.path.join(folder_path, 'variables.csv')
            
            # Write CSV file (plain lines with all columns)
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Write data with all columns
                for row in data_list:
                    var = str(row['Variable']).replace('\n', ' ')
                    val = row['Value']
                    lower = row['LowerBound']
                    upper = row['UpperBound']
                    dtype = row['Type']
                    units = row['Units']
                    csvfile.write(f"{var},{val},{lower},{upper},{dtype},{units}\n")
            
            files_created[folder_path] = {
                'csv_file': csv_file_path,
                'variable_count': len(data_list)
            }
            
            # Removed verbose print statement for cleaner output
        
        return files_created
        
    except Exception as e:
        print(f"Error processing file: {e}")
        return {}


# Example usage:
if __name__ == "__main__":
    # Example usage of the functions
    file_path = "run_1.txt"  # Replace with your actual file path
    
    print("=== Organizing ALL values into folders ===")
    files_created = organize_values_to_folders(file_path, "organized_data")
    
    print(f"\nCreated {len(files_created)} folders with CSV files:")
    for folder, info in list(files_created.items())[:10]:  # Show first 10
        print(f"  {folder}: {info['variable_count']} variables")
    
    if len(files_created) > 10:
        print(f"  ... and {len(files_created) - 10} more folders")
    
    print("\n" + "="*60)
    print("\n=== Organizing specific path prefix ===")
    
    # Example: Organize only Plant.Absorber variables
    specific_files = organize_specific_path(file_path, "Plant.Absorber", "specific_absorber_data")
    
    print(f"\nCreated {len(specific_files)} folders for Plant.Absorber:")
    for folder, info in specific_files.items():
        print(f"  {folder}: {info['variable_count']} variables")
    
    print("\n" + "="*60)
    print("\n=== Reading specific values (original functionality) ===")
    
    # Read a specific value
    path_name = "Plant.Hold_up"
    value = read_value_from_txt(file_path, path_name)
    if value is not None:
        print(f"Value for '{path_name}': {value}")
    
    # Read all values with a prefix
    absorber_values = read_matching_values_from_txt(file_path, "Plant.Absorber.D_CO2")
    print(f"\nFound {len(absorber_values)} D_CO2 values in Absorber:")
    for path, val in list(absorber_values.items())[:5]:  # Show first 5 entries
        print(f"  {path}: {val}")
