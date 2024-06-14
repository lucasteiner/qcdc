
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
        parse_censo_file (ser['RootFile'], ser)

    return ser

def parse_censo_file(file_path, result_dict):
    with open(file_path, 'r') as file:
        content = file.read()

    # Regex pattern to find lines with the required information
    main_pattern = re.compile(r'^\s*(CONF\d+)\s+(-?\d+\.\d+(\s+-?\d+\.\d+)*\s+<------)\s*$', re.MULTILINE)
    boltzmann_pattern = re.compile(r'^Conformers that are below the Boltzmann threshold G_thr\(2\) of 99\.0%:\s*(.*?)$', re.MULTILINE | re.DOTALL)
    
    matches = main_pattern.findall(content)

    if matches:
        last_match = matches[-1]
        result_dict['conf'] = last_match[0]
        result_dict['values'] = re.findall(r'-?\d+\.\d+', last_match[1])

    boltzmann_matches = boltzmann_pattern.findall(content)
    
    if boltzmann_matches:
        boltzmann_lines = boltzmann_matches[0].split('\n')
        result_dict['boltzmann_conformers'] = [line.strip() for line in boltzmann_lines if line.strip()]

    return result_dict