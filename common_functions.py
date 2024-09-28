import my_constants as mc
import os
import numpy as np
import re
from molmass import Formula
from scipy.constants import h, k, c, N_A, R, pi, milli
from pymatgen.core.structure import Molecule
from pymatgen.symmetry.analyzer import PointGroupAnalyzer

#this file contains functions which are used by both, 
#the turbomole parser and orca parser
def set_paths (ser, root, filename):
    """ Sets some useful path combinations """
    ser['Folder'] = root.split(os.sep)[-1] #name of folder only
    ser['Group'] = root.strip(str(ser['Folder'])) #name of root without folder
    ser['Root'] = root
    ser['File'] = filename
    ser['RootFile'] = root+'/'+filename
   

def parse_xyz(file_path):
    """ Extracts number of atoms, coordinates and element symbols from file in xyz format"""
    # Read the file content
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # Number of atoms
    num_atoms = int(lines[0].strip())
    
    # Comment line
    comment = lines[1].strip()
    
    # Elements and coordinates
    elements = []
    coordinates = []
    
    # Parse each atom data line
    for line in lines[2:num_atoms+2]:  # Only read the number of atoms specified
        parts = line.split()
        elements.append(parts[0])
        coordinates.append(tuple(map(float, parts[1:4])))
        
    return num_atoms, comment, coordinates, elements


#Regex searches for 3 floats and one element symbol
RE_COORD = re.compile("([-+]?\d*\.\d+)[ ]+([-+]?\d*\.\d+)[ ]+([-+]?\d*\.\d+)[ ]+([a-zA-Z]{1,2})")
def get_coord3(root, dat='coord'):
    """Reads coord file and returns xyz coordinates in bohr"""
    with open(root+os.sep+dat) as file:
        xyzelem = re.findall(RE_COORD, file.read())
        if bool(xyzelem):
            xyzelem = np.asarray(xyzelem)
            return (xyzelem[:,:3].astype(float), xyzelem[:,3]) #atomic units
        else:
            return (None, None)
        #return xyzelem[:,:3].astype(float)*BOHR2ANGSTROM, xyzelem[:,3]

def write_xyz(elements, coordinates, file_path, comment="Generated by script", bottom_info=None):
    """
    Write elements and coordinates to a file in XYZ format.

    Parameters:
    elements (list of str): List of element symbols.
    coordinates (list of list of float): Nx3 list of coordinates.
    file_path (str): Path to the output file.
    comment (str): Comment line to be included in the output file.
    bottom_info: Can include a string with charge, dipole, zero point energy, solvation model, frequencies
    """
    if len(elements) != len(coordinates):
        raise ValueError("The number of elements must match the number of coordinate sets.")

    with open(file_path, 'w') as file:
        # Write the number of atoms
        file.write(f"{len(elements)}\n")
        # Write the comment line
        file.write(f"{comment}\n")
        # Write the element symbols and coordinates
        for element, coord in zip(elements, coordinates):
            file.write(f"{element} {coord[0]:.6f} {coord[1]:.6f} {coord[2]:.6f}\n")
        if bottom_info:
            file.write(bottom_info)
        
def format_properties(charge=None, s2=None, dipole=None, vibration=None, zpe=None):
    """
    Format properties into a specified string format.

    Parameters:
    charge (float): The charge value.
    s2 (float): The s2 value.
    dipole (list of float): The dipole moment components.
    vibration (list of float): The vibrational frequencies.
    zpe (float): The zero-point energy.

    Returns:
    str: Formatted string containing the properties.
    """
    lines = []

    if charge is not None:
        lines.append(f"$charge\n{charge}")

    if s2 is not None:
        lines.append(f"$s2\n{s2:.3f}")

    if dipole is not None:
        dipole_str = ' '.join(f"{d:.14f}" for d in dipole)
        lines.append(f"$dipole\n{dipole_str}")

    if vibration is not None:
        vibration_str = ' '.join(f"{v:.2f}" for v in vibration)
        lines.append(f"$vibration\n{vibration_str}")

    if zpe is not None:
        lines.append(f"$zpe\n{zpe:.7f}")

    # only append the end syntax in case we append some additional information, to preserve the file format
    if bool(lines):
        lines.append("$end")

    return '\n'.join(lines)

def read_xyz(file_path):
    """
    Reads an XYZ file and extracts the number of atoms, comment line, elements, and coordinates.

    Parameters:
    file_path (str): Path to the XYZ file.

    Returns:
    tuple: A tuple containing:
        - num_atoms (int): The number of atoms.
        - comment (str): The comment line.
        - elements (list of str): The list of element symbols.
        - coordinates (list of list of float): The Nx3 list of coordinates.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Number of atoms is the first line
    num_atoms = int(lines[0].strip())
    # Comment line is the second line
    comment = lines[1].strip()
    # Elements and coordinates start from the third line
    elements = []
    coordinates = []

    for line in lines[2:]:
        parts = line.split()
        if len(parts) == 4:
            elements.append(parts[0])
            coordinates.append([float(parts[1]), float(parts[2]), float(parts[3])])
    #print('Elements', elements)

    return num_atoms, comment, elements, coordinates

def moment_of_inertia(coords,mass,i,j):
    """
    Calculates Moment of inertia for x(i=1,j=2), y(i=0,j=2) or z(i=0,j=1) direction
    coords : np.array with dimension (N,3) contains xyz coordinates of each atom.
    mass : np.array with dimension (N) containing molar mass of each atom.
    """
    return np.sum(mass * (coords[:,i]*coords[:,i]+coords[:,j]*coords[:,j]))

def center_of_mass(coords, mass):
    """takes np arrays of coordinates and masses and calculates center of mass from that"""
    #print(coords, mass)
    return np.average(coords, axis=0, weights=mass)

def mass_of_elements(elems):
    """
    Takes list of element strings and converts the most frequently abundant isotope to the corresponding mass
    Probably it would be faster to write a dictionary but this is more convenient for now
    """
    return [Formula(elem.capitalize()).isotope.mass for elem in elems]

def zero_point_energy(frequencies):
    """
    takes array of positive non-zero frequencies in wavenumbers and
    returns zero point energy in kJ/mol
    """
    return 0.5 * np.sum(frequencies)*mc.WAVENUMBERS2KJMOL

def translational_partition_function(mass, volume=mc.MOLES * R * mc.TEMPERATURE / mc.PRESSURE, temperature=mc.TEMPERATURE, n_part = mc.MOLES):
    """
    takes the molar mass [g/mol] of a molecule and
    returns the translational partition function (ideal gas)
    default volume is molar volume of ideal gases, 
    choose a volume of 0.001 m^3 for liquids
    """
    mass = mass/1000/N_A#kg
    return (mass*temperature*2*pi*k/h/h)**1.5 * volume /n_part/N_A

def vibrational_partition_function(frequencies, temperature=mc.TEMPERATURE):
    """
    takes array of positive non-zero frequencies and
    returns vibrational partition function
    """
    return np.prod(1/(1-np.exp(-frequencies*100 *c*h/k/temperature)))

def rotational_partition_function(moments_of_inertia, sigma=1, temperature=mc.TEMPERATURE):
    """
    takes moments of inertia (np.array) and 
    returns rotational partition function
    sigma : symmetry number
    """
    return (temperature*temperature*temperature * np.prod(moments_of_inertia))**0.5 / sigma * mc.CONSTANTX 
    # mc.CONSTANTX : *pi**0.5 * ((8*pi*pi*k/h/h)**3 *(mc.AMU**3*mc.BOHR2METER**6))**0.5

def chemical_potential(zero_point_energy, q_translation, q_vibration, q_rotation, temperature=mc.TEMPERATURE):
    """
    takes partition functions (q) and zero point energy and
    returns chemical potential in kJ/mol (Gibbs free energy)
    """
    return zero_point_energy - R*temperature*np.log(q_translation*q_vibration*q_rotation)/1000 

def calc_grimme_short (freq_cm, temperature=mc.TEMPERATURE):
    """
    takes np array with positive vibrational frequencies in wavenumbers
    Return value corrects the Gibbs free enthalpy.
    """
    Bav = 1e-44 #kg*m^2
    freq_s = freq_cm*100.0*c #1/s
    xx = freq_s*h/k/temperature #no unit
    #print('xx=',xx)
    Sv = xx * (1.0 / (np.exp(xx)-1.0))  -  np.log(1.0 - np.exp(-xx)) #no unit
    mue = h/(8.0 * pi**2.0 * freq_s) #J*s^2 = kgm^2
    Sr = (1 + np.log(8.0 *pi*pi*pi *mue*Bav / (mue + Bav) *k*temperature /h/h) ) / 2 #no unit
    w_damp = 1.0 / (1.0 + (1e2/freq_cm)**4) #m^4
    S_final = w_damp*R*Sv + ( (1.0-w_damp) *R*(1 + np.log(8.0*pi*pi*pi*mue*Bav /(mue + Bav) *k*temperature/h/h) ) /2) #m^4*J/mol/K
    return np.sum((S_final - R*Sv )*milli)*temperature #m^4*kJ/mol

#Frequency dependent stuff could be moved into different function,
#such that this can be executed for all calculations
def derive_data (ser, elements, coordinates, frequencies, temperature=mc.TEMPERATURE):
    """
    This function derives all kind of physical data from the collected values
    Frequencies are needed for most of the values
    """
    # We need mass information of the elements
    # molecular mass
    coordinates = np.array(coordinates)
    bohr_coordinates = coordinates * mc.ANGSTROM2BOHR
    elem_masses =  mass_of_elements(elements) #g/mol)
    ser[mc.M_MASS] = np.sum (elem_masses) #g/mol)

    # Calculate Partition Functions
    ser['Translational Partition Function'] = translational_partition_function(ser[mc.M_MASS])
    ser['Translational Partition Function for Liquids'] = translational_partition_function(ser[mc.M_MASS], volume=1e-3)

    ser['Point Group'], ser['Symmetry Number'] = determine_point_group_and_symmetry_number(elements, coordinates)
    if ser['Symmetry Number'] is None:
        raise KeyError(f"No symmetry number assigned for Point Group {ser['Point Group']}, please add it to symmetry_number_lookup")

    if len(coordinates) == 1:
        ser['Single Atom'] = True
        return
        # to be implemented

    ser['Linear Molecule'] = is_molecule_linear(coordinates)
    if ser['Linear Molecule']:
        return
        # to be implemented

    # Calculate moments of inertia I (amu/bohr^2)'
    # We need centralized coordinates
    xyz_central = bohr_coordinates - center_of_mass(bohr_coordinates, elem_masses)
    ser['I_xx'] = moment_of_inertia(xyz_central, elem_masses, 1, 2)
    ser['I_yy'] = moment_of_inertia(xyz_central, elem_masses, 0, 2)
    ser['I_zz'] = moment_of_inertia(xyz_central, elem_masses, 0, 1)
    momi = np.asarray([ser['I_xx'], ser['I_yy'], ser['I_zz']]) 

    # Ignore frequencies 
    frequencies = np.array(frequencies)
    positive_frequencies = frequencies[frequencies > 0]

    # Calculate Partition Functions
    ser['Translational Partition Function'] = translational_partition_function(ser[mc.M_MASS])
    ser['Translational Partition Function for Liquids'] = translational_partition_function(ser[mc.M_MASS], volume=1e-3)
    ser['Rotational Partition Function'] = rotational_partition_function(momi, sigma=ser['Symmetry Number'])

    ser['Vibrational Partition Function'] = vibrational_partition_function(positive_frequencies)
    ser['Zero Point Energy'] = zero_point_energy(positive_frequencies)
    ser['Chemical Potential'] = chemical_potential(ser['Zero Point Energy'], ser['Translational Partition Function'],
                                                   ser['Vibrational Partition Function'], ser['Rotational Partition Function'])
    ser['Chemical Potential for Liquids'] = chemical_potential(ser['Zero Point Energy'], ser['Translational Partition Function for Liquids'],
                                                   ser['Vibrational Partition Function'], ser['Rotational Partition Function'])

    # Calculate and Apply Correcture Term for Vibrational Partition Function
    low_positive_frequencies = positive_frequencies[positive_frequencies < mc.QRRHO_CUTOFF]
    ser['qRRHO'] = calc_grimme_short(low_positive_frequencies, temperature)
    ser['Chemical Potential'] -= ser['qRRHO']
    ser['Chemical Potential for Liquids'] -= ser['qRRHO']

    # Calculate Partition Functions with sign inversion for imaginary frequencies smaller than 100 in magnitude. Change value in config file.
    sign_inverted_frequencies = frequencies[np.abs(frequencies) > 0]
    sign_inverted_frequencies[sign_inverted_frequencies <= mc.SIGN_INV_THR] = None
    sign_inverted_frequencies[sign_inverted_frequencies > mc.SIGN_INV_THR] = np.abs(sign_inverted_frequencies[sign_inverted_frequencies > mc.SIGN_INV_THR])


    # Calculate Partition Functions which are effected by sign inversion in frequencies
    ser['Chemical Potential (sign inverted)'] = chemical_potential(zero_point_energy(sign_inverted_frequencies), ser['Translational Partition Function'],
                                                   vibrational_partition_function(sign_inverted_frequencies), ser['Rotational Partition Function'])
    ser['Chemical Potential for Liquids (sign inverted)'] = chemical_potential(zero_point_energy(sign_inverted_frequencies), ser['Translational Partition Function for Liquids'],
                                                   vibrational_partition_function(sign_inverted_frequencies), ser['Rotational Partition Function'])

    # Calculate and Apply Correcture Term for Vibrational Partition Function
    low_sign_inverted_frequencies = sign_inverted_frequencies[sign_inverted_frequencies < mc.QRRHO_CUTOFF]
    ser['qRRHO (sign inverted)'] = calc_grimme_short(low_sign_inverted_frequencies, temperature)
    ser['Chemical Potential (sign inverted)'] -= ser['qRRHO (sign inverted)']
    ser['Chemical Potential for Liquids (sign inverted)'] -= ser['qRRHO (sign inverted)']


def is_molecule_linear(coordinates):
    """
    Check if a molecule is linear based on its xyz coordinates.

    Parameters:
    coordinates (list of tuples): List of (x, y, z) coordinates of the molecule's atoms.

    Returns:
    bool: True if the molecule is linear, False otherwise.
    """
    if len(coordinates) < 3:
        # A molecule with less than 3 atoms is always linear
        return True

    # Calculate vectors between consecutive points
    vectors = []
    for i in range(1, len(coordinates)):
        vec = np.array(coordinates[i]) - np.array(coordinates[i - 1])
        vectors.append(vec)

    # Check if all vectors are linearly dependent
    # We do this by checking the cross product of consecutive vectors
    for i in range(1, len(vectors)):
        cross_product = np.cross(vectors[i - 1], vectors[i])
        if not np.allclose(cross_product, 0):
            return False

def extract_conf_number(input_string):
    """
    Extracts the number next to '/CONF' in the input string.

    Parameters:
    input_string (str): The input string to search for the pattern.

    Returns:
    int or None: The extracted number if found, otherwise None.
    """
    # Define the regular expression pattern to match '/CONF' followed by digits
    pattern = r'/CONF(\d+)'
    
    # Search for the pattern in the input string
    match = re.search(pattern, input_string)
    
    # If a match is found, extract the number and return it
    if match:
        return int(match.group(1))
    
    # If no match is found, return None
    return None


symmetry_number_lookup = {
    "C1": 1,
    "Cs": 1,
    "Ci": 2,
    "C2": 2,
    "C2v": 2,
    "C2h": 2,
    "C3": 3,
    "C3v": 3,
    "C3h": 3,
    "C4": 4,
    "C4v": 4,
    "C4h": 4,
    "C6": 6,
    "C6v": 6,
    "C6h": 6,
    "D2": 4,
    "D2h": 4,
    "D2d": 4,
    "D3": 6,
    "D3h": 6,
    "D3d": 6,
    "D4": 8,
    "D4h": 8,
    "D4d": 8,
    "D6": 12,
    "D6h": 12,
    "D6d": 12,
    "Td": 12,
    "Oh": 24,
    "I": 60,
    "S4": 4,
    "S6": 4,
    "C*v": 1,  # Linear heteronuclear (C*v as replacement for C infinity v)
    "D*h": 2,  # Linear homonuclear (D*h as replacement for D infinity h)
}
#https://chem.libretexts.org/Bookshelves/Inorganic_Chemistry/Chemical_Group_Theory_(Miller)/02%3A_Rotational_Symmetry/2.02%3A_Point_Groups

def determine_point_group_and_symmetry_number(elements, coordinates):
    """
    Determines the point group and symmetry number (sigma) for calculating the rotational partition function,
    including special cases for linear molecules and single atoms.

    Args:
        elements (list): A list of chemical element symbols (e.g., ['H', 'O', 'H']).
        coordinates (list of lists): A 3xN list of coordinates for the corresponding elements (e.g., [[x1, y1, z1], [x2, y2, z2], ...]).

    Returns:
        tuple: A tuple containing the point group of the molecule and its symmetry number (sigma) for the rotational partition function.
    """
    # Check if it's a single atom
    if len(elements) == 1:
        return "Single Atom", 1  # Single atom, sigma = 1

    capital_elements = [element.capitalize() for element in elements]
    # Create the Molecule object using pymatgen
    molecule = Molecule(capital_elements, coordinates)

    # Perform point group analysis
    analyzer = PointGroupAnalyzer(molecule)

    # Get the point group
    point_group = str(analyzer.get_pointgroup())

    symmetry_number = symmetry_number_lookup.get(point_group, None)  # Default to None if not found

    return point_group, symmetry_number
    #return str(None), symmetry_number



