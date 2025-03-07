import os
import re

import common_functions
import my_constants as mc
import numpy as np


def parse_turbomole(root, dirs, files):
    """
    Parses Turbomole calculation files.
    """
    ser = {}

    filename = 'control'
    filename2 = 'ohess.out'
    filename3 = 'xtb.out'
    filename4 = 'cosmotherm.out'
    if filename in files:
        common_functions.set_paths(ser, root, filename)
        get_control2(ser, root, filename)
        ser['Type of Calculation'] = 'turbomole'
    elif filename2 in files:
        ser['Type of Calculation'] = 'xtb'
        common_functions.set_paths(ser, root, filename2)
    elif filename3 in files:
        ser['Type of Calculation'] = 'xtb'
        common_functions.set_paths(ser, root, filename3)
    elif filename4 in files:
        ser['Type of Calculation'] = 'cosmors (only)'
        common_functions.set_paths(ser, root, filename4)
    else:
        return

    filename = 'energy'
    if filename in files:
        ser['Single Point Energy'] = get_energy2(root)[0] * mc.EH2KJMOL

    filename = 'coord'
    if filename in files:
        (xyz, elem) = common_functions.get_coord3(root)
        if xyz is not None:
            ser['xyz Coordinates'] = xyz * mc.BOHR2ANGSTROM
            ser['Elements'] = elem
            ser['xyz File Name'] = f'./xyz/{(root[2:] + f"/{filename}").replace("/", "_")}.xyz'

    filename = 'xtbopt.xyz'
    if filename in files:
        ser['Number of Atoms'], _, ser['Elements'], ser['xyz Coordinates'] = \
            common_functions.read_xyz(os.path.join(root, filename))
        ser['xyz File Name'] = f'./xyz/{(root[2:] + f"/{filename}").replace("/", "_")}.xyz'

    filename = 'xtbopt.coord'
    if filename in files and ser['Type of Calculation'] == 'xtb':
        (xyz, elem) = common_functions.get_coord3(root, filename)
        if xyz is not None:
            ser['xyz Coordinates'] = xyz * mc.BOHR2ANGSTROM
            ser['Elements'] = elem
            ser['xyz File Name'] = f'./xyz/{(root[2:] + f"/{filename}").replace("/", "_")}.xyz'

    filename = 'vibspectrum'
    if filename in files:
        tmp = get_vibspectrum(root)
        ser['Frequencies'] = sorted(tmp)
        ser['Frequency Calculation'] = True

    filename = 'eiger.out'
    if filename in files:
        get_eiger(ser, root)

    # parses for the calculation named 'out'
    filenames = ['out.tab', 'cosmotherm.tab']
    [get_cosmors(ser,root,filename) for filename in filenames if filename in files]
    #for filename in filenames:
    #    if filename in files:
    #        get_cosmors(ser, root, filename)

    #filename = 'out.tab'
    #if filename in files:
    #    get_cosmors(ser, root, filename)
    
    return ser

def get_control2(ser, root, filename):
    """
    Scans the text and produces tokens from the control file.
    """
    with open(os.path.join(root, filename)) as file:
        string = file.read()
        tokens = string.split('$')
        for token in tokens:
            if token.startswith('cosmo\n'):
                ser['Cosmo'] = dict(re.findall(equality_re, token))
            elif token.startswith('rundimensions'):
                ser['RunDimensions'] = dict(re.findall(equality_re, token))
            elif token.startswith('forceupdate'):
                ser['ForceUpdate'] = dict(re.findall(equality_re, token))
            elif token.startswith('scfdamp '):
                ser['SCFDamp'] = dict(re.findall(equality_re, token))
            elif token.startswith('fermi'):
                ser['Fermi'] = dict(re.findall(equality_re, token))
            elif token.startswith('scfconv '):
                ser['SCFConv'] = int(token.split()[1])
            elif token.startswith('rij'):
                ser['RI'] = True
            elif token.startswith('dft'):
                ser['DFT'] = right_words(['functional', 'gridsize'], token)
            elif token.startswith('atoms'):
                ser['BasisForElement'] = dict(re.findall(equality_basis_re, token))
                ser['BasisSet'] = set(ser['BasisForElement'].values())
                if len(ser['BasisSet']) == 1:
                    ser['BasisForElement'] = None
            elif token.startswith('disp'):
                ser['Dispersion'] = token.strip('\n')
            elif token.startswith('dipole from ridft'):
                ser['Dipole'] = extract_dipole_moment_components(token)
            elif token.startswith('ssquare'):
                ser['S2'] = float(token.split()[3])
        ser['filenames'] = dict(re.findall(r'\$(\S*)\s[^$]*?\sfile=(\S*)', string, re.DOTALL))


equality_re = re.compile(r"(\S+)\s*=\s*(\S+)")
equality_basis_re = re.compile(r"=([a-z]{1,2})\s(\S+)")

def extract_dipole_moment_components(text):
    """
    Extracts the dipole moment components (x, y, z) and the total dipole moment from the given text.

    Parameters:
        text (str): The input text containing the dipole moment information.
    
    Returns:
        dict: A dictionary with 'x', 'y', 'z', and 'total' dipole moments in appropriate units.
    """
    # Regex for extracting x, y, z components of dipole moment
    xyz_pattern = r"x\s+([-+]?\d+\.\d+)\s+y\s+([-+]?\d+\.\d+)\s+z\s+([-+]?\d+\.\d+)"
    # Regex for extracting total dipole moment
    total_pattern = r"\| dipole \| =\s+([\d\.]+)"
    
    xyz_match = re.search(xyz_pattern, text)
    total_match = re.search(total_pattern, text)

    if xyz_match and total_match:
        return {
            "x": float(xyz_match.group(1)),
            "y": float(xyz_match.group(2)),
            "z": float(xyz_match.group(3)),
            "total": float(total_match.group(1))
        }
    
    return None  # Return None if parsing fails


def right_words(substringlist, string):
    """
    Returns right word of substring for a list of substrings.
    """
    return {substring: re.search(substring + r"[ \t]*([^\n\r]*)", string)[1]
            for substring in substringlist}


RE_VIBSPECTRUM = re.compile(r"[-+]?\d*\.*\d+[ a]+([-+]?\d*\.*\d+)")


def get_vibspectrum(root):
    """
    Extracts information (frequencies) from 'vibspectrum'.
    """
    with open(os.path.join(root, 'vibspectrum')) as file:
        return [float(match) for match in re.findall(RE_VIBSPECTRUM, file.read())]


def get_cosmors(ser, root, dat='out.tab'):
    with open(os.path.join(root, dat)) as file:
        for line in file:
            if 'out' in line:
                ser['CosmoRS'] = float(line[80:])*mc.CAL2J


def get_eiger(ser, root, dat='eiger.out'):
    with open(os.path.join(root, dat)) as file:
        for line in file:
            if 'HOMO:' in line:
                ser['HOMO'] = float(line[28:39])
                ser['n_MO (HOMO)'] = float(line.split()[1])
            if 'LUMO:' in line:
                ser['LUMO'] = float(line[28:39])
                ser['n_MO (LUMO)'] = float(line.split()[1])


RE_ENERGY = re.compile(r"^[0-9 ]{6}\s+([-+]?\d*\.\d+)\s+([-+]?\d*\.\d+)\s+([-+]?\d*\.\d+)")


def get_energy2(root, dat='energy'):
    """
    Returns vector with element[0]: total energy [1]:kinetic energy, [2]:potential energy.
    """
    with open(os.path.join(root, dat)) as file:
        return np.array(re.findall(RE_ENERGY, file.readlines()[-2])[0]).astype(float)
