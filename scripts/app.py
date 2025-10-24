import sys
import os
from analyse import organize_values_to_folders

def get_user_input():
    """Get file name and output directory from user input"""
    print("=== Text File Organizer ===")
    print()
    
    # Get input file name
    while True:
        file_path = input("Enter input file name (or press Enter for 'Trials/run1/run_1.txt'): ").strip()
        if not file_path:
            file_path = "Trials/run1/run_1.txt"
        
        # Check if file exists
        if os.path.exists(file_path):
            break
        else:
            print(f"Error: File '{file_path}' not found. Please try again.")
    
    # Automatically generate output directory based on input file path
    if "Trials" in file_path:
        # Extract the part after "Trials/"
        trials_index = file_path.find("Trials/")
        if trials_index != -1:
            # Get everything after "Trials/"
            relative_path = file_path[trials_index + len("Trials/"):]
            # Remove the filename and keep only the directory structure
            relative_dir = os.path.dirname(relative_path)
            # Construct output directory under "Corrections"
            default_output = f"Trials/{relative_dir}/organized_output"
        else:
            default_output = "Trials/organized_output"
    else:
        default_output = "Trials/organized_output"

    # Get output directory
    output_dir = input(f"Enter output directory (or press Enter for '{default_output}'): ").strip()
    if not output_dir:
        output_dir = default_output
    
    return file_path, output_dir

def main():
    """
    Main execution function - organize values from txt file into folder structure
    """
    
    # Get user input
    file_path, output_dir = get_user_input()
    
    print()
    print(f"Processing file: {file_path}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Organize ALL values into folders
    files_created = organize_values_to_folders(file_path, output_dir)
    
    if files_created:
        total_variables = sum(info['variable_count'] for info in files_created.values())
        print(f"All files stored successfully. Created {len(files_created)} folders with {total_variables} variables.")
    else:
        print("Error: No data was organized or file not found.")

if __name__ == "__main__":
    main()
