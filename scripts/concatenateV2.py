import os
import sys
from datetime import datetime

def format_scientific_notation(value_str):
    try:
        num = float(value_str)
        if num == 0.0:
            return "0.0000000000000000e+00"
        else:
            return f"{num:.16e}"
    except (ValueError, TypeError):
        return value_str


def read_csv_in_folder_order(base_folder):
    """Walk folders in deterministic order and read variables.csv in file order.

    Returns list of dicts with keys: path, value, lower_bound, upper_bound, type, units
    """
    variables = []
    # Use os.walk but sort dirs and files to make traversal deterministic
    for root, dirs, files in os.walk(base_folder):
        dirs.sort()  # ensures parent folders come before children in listing
        files.sort()
        for fname in files:
            if fname != 'variables.csv':
                continue
            file_path = os.path.join(root, fname)
            # compute path prefix relative to base_folder
            rel = os.path.relpath(root, base_folder)
            if rel == '.':
                prefix = ''
            else:
                prefix = rel.replace(os.sep, '.') + '.'
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split(',')
                        if len(parts) >= 6:
                            var = parts[0].strip()
                            value = parts[1].strip()
                            lower = parts[2].strip()
                            upper = parts[3].strip()
                            dtype = parts[4].strip()
                            units = parts[5].strip()
                        elif len(parts) >= 2:
                            var = parts[0].strip()
                            value = parts[1].strip()
                            lower = "-1.00000e+20"
                            upper = "1.00000e+20"
                            dtype = "Notype"
                            units = ''
                        else:
                            continue
                        variables.append({
                            'path': prefix + var,
                            'value': value,
                            'lower_bound': lower,
                            'upper_bound': upper,
                            'type': dtype,
                            'units': units,
                        })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    return variables


def write_reconstructed(variables, output_file):
    out_dir = os.path.dirname(output_file)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)
        print(f"Created directory: {out_dir}")
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write(f"#!gSTORE-4 created on {datetime.now().strftime('%a %b %d %H:%M:%S %Y')}\n")
        out.write("# PROCESS reconstructed_process\n\n")
        out.write("!Time\n\t0\n\n")
        out.write("# The total number of variables in the process\n")
        out.write(f"# {len(variables)}\n")
        out.write("# Note: all variables are saved\n")
        out.write("!Variables\n")
        out.write("\t# PathName : Value : LowerBound : UpperBound : Type : Units\n")
        for v in variables:
            value_sci = format_scientific_notation(v['value'])
            lower_sci = format_scientific_notation(v['lower_bound'])
            upper_sci = format_scientific_notation(v['upper_bound'])
            if v['units'].strip():
                line = f"\t{v['path']} : {value_sci} : {lower_sci} : {upper_sci} : {v['type']} : {v['units']}\n"
            else:
                line = f"\t{v['path']} : {value_sci} : {lower_sci} : {upper_sci} : {v['type']} :\n"
            out.write(line)
    print(f"Wrote {len(variables)} variables to {output_file}")


def get_run_and_paths():
    run_name = ''
    if len(sys.argv) > 1:
        run_name = sys.argv[1]
    else:
        run_name = input("Enter run name (e.g., run1) or press Enter for 'run1': ").strip() or 'run1'
    input_folder = os.path.join('Trials', run_name, 'organized_output')
    output_file = os.path.join('Corrections', run_name, 'reconstructed_v2.txt')
    return input_folder, output_file


def main():
    input_folder, output_file = get_run_and_paths()
    if not os.path.isdir(input_folder):
        print(f"Input folder not found: {input_folder}")
        return
    vars = read_csv_in_folder_order(input_folder)
    if not vars:
        print("No variables found")
        return
    write_reconstructed(vars, output_file)


if __name__ == '__main__':
    main()
