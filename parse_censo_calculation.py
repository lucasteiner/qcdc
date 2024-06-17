
import os
import re

import common_functions
import my_constants as mc
import numpy as np


def parse_censo(root, dirs, files):
    """
    Parses Censo calculation files.
    """
    ser = {}

    filename = 'censo.out'
    if filename in files:
        common_functions.set_paths(ser, root, filename)
        ser['Type of Calculation'] = 'censo'

        #do default parsing operations
        ser['censo conformers'], best_values = parse_censo_file (ser['RootFile'])
        for (key, value) in zip (censo_columns, best_values):
            ser[key] = value
        #parse_censo_file (ser['RootFile'], ser)

    return ser


# Columns for the table
censo_columns = ["CONF#", "E(GFNn-xTB)", "ΔE(GFNn-xTB)", "E [Eh]", "Gsolv [Eh]", "GmRRHO [Eh]", "Gtot", "ΔGtot", "Boltzmannweight"]

# Pattern to match the table header
header_pattern = re.compile(r"CONF#\s+E\(GFNn-xTB\)\s+ΔE\(GFNn-xTB\)\s+E\s\[Eh\]\s+Gsolv\s\[Eh\]\s+GmRRHO\s\[Eh\]\s+Gtot\s+ΔGtot\s+Boltzmannweight")

# This only works if headers match censo headers (mRRHO has to be switched on)
# And only for part 2 and part 3?
def parse_censo_file(file_path):
    all_data = []
    all_lowest_conformers = []
    with open(file_path, 'r') as file:
        lines = file.readlines()

        for i, line in enumerate(lines):
            data = []
            lowest_conformer = []
            if header_pattern.search(line):
                # Skip the header and the two following metadata lines
                for j in range(i + 3, len(lines)):
                    if lines[j].strip() == "":  # Stop if we reach an empty line
                        all_data.append(data)
                        all_lowest_conformers.append(lowest_conformer)
                        break
                    row = re.split(r'\s+', lines[j].strip())
                    if len(row) == len(censo_columns):
                        data.append(row)
                    elif len(row) == len(censo_columns) + 1:
                        lowest_conformer = row[:-1]
                        data.append(lowest_conformer)

    #print(data)
    #print(lowest_conformer)
    return all_data[-1], all_lowest_conformers[-1]


# This is not really needed anymore,
# but it also finds the result of the Boltzmann sum
# However, applying the Boltzmann sum does only make sense with a proper preprocessing of the geometries.
# Let's implement Boltzmann sum later when needed. This function stays for now, in case I need the old Boltzmann sum (e.g. for comparison)

#def parse_censo_file_save(file_path, result_dict):
#    with open(file_path, 'r') as file:
#        content = file.read()
#
#    # Regex pattern to find lines with the required information
#    main_pattern = re.compile(r'^\s*(CONF\d+)\s+(-?\d+\.\d+(\s+-?\d+\.\d+)*\s+<------)\s*$', re.MULTILINE)
#    boltzmann_pattern = re.compile(r'^Conformers that are below the Boltzmann threshold G_thr\(2\) of 99\.0%:\s*(.*?)$', re.MULTILINE | re.DOTALL)
#    
#    matches = main_pattern.findall(content)
#
#    if matches:
#        last_match = matches[-1]
#        result_dict['conf'] = last_match[0]
#        result_dict['values'] = re.findall(r'-?\d+\.\d+', last_match[1])
#
#    boltzmann_matches = boltzmann_pattern.findall(content)
#    
#    if boltzmann_matches:
#        boltzmann_lines = boltzmann_matches[0].split('\n')
#        result_dict['boltzmann_conformers'] = [line.strip() for line in boltzmann_lines if line.strip()]
#
#    return result_dict
