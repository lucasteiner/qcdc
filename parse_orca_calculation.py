import common_functions
import my_constants as mc
import re

def parse_orca(root, dirs, files):
    """
    function parses orca files and returns content as dict
    """
    orca_filenames = filter_orca_filenames(files, root)
    calculations = []
    #print(orca_filenames)
    for filename in orca_filenames:

        #ser reflects one series, although we use dict to be faster
        ser = dict()
        ser['Type of Calculation'] = 'orca'

        #save path and filename related variables in ser
        common_functions.set_paths(ser, root, filename)

        #extract orca input from output
        _, input_file = extract_orca_input(ser ['RootFile'])
        parse_orca_input (ser, input_file, files)
        



        #do default parsing operations
        parse_file ( ser['RootFile'], ser )

        if ser['Potential Energy Surface Scan']:
            #parse scan-file
            ser ['Surface'] = parse_scan_file(ser['RootFile'])

        if filename.endswith('.out'):
            ser ['BaseName'] = filename[:-4]
            xyz_file = ser['BaseName']+'.xyz'
        else:
            ser ['BaseName'] = filename
            xyz_file = filename+'.xyz'
        ser['xyz File Name'] = './xyz/'+(ser['Root'][2:] + '/' + xyz_file).replace('/','_')


        #read and save coordinate data of cooresponding .out file
        # yet we use the -.xyz file, which is not ideal...
        # after changing this, the BaseName above is not necessary anymore
        if xyz_file in files:
            ser['Number of Atoms'], _, ser['Elements'], ser['xyz Coordinates'] = common_functions.read_xyz (root + '/' + xyz_file)
        
        frequencies = None
        if ser['Frequency Calculation']:
            ser['Frequencies'] = extract_last_vibrational_frequencies (ser['RootFile'], ser['Number of Atoms']*3)


        
        #thermodynamic calculations
        #if xyz_content:

        calculations.append(ser)
    return calculations


    

def filter_orca_filenames(filenames, root):
    """
    Filters a list of filenames based on specific criteria and returns valid filenames.

    Args:
        filenames (list): A list of filenames to be filtered.

    Returns:
        list: A list containing valid filenames that meet the specified criteria.

    Example:
        >>> file_list = ["file1.out", "file2.out", "xtb.out", "file3.txt"]
        >>> filtered_files = filter_filenames(file_list)
        >>> print(filtered_files)
    """


    # List of invalid filenames to be excluded
    invalid_filenames = ['xtb.out','crest.out','censo.out']

    # Initialize a list to store valid filenames
    valid_filenames = []

    # Iterate through each filename in the input list
    for filename in filenames:
        # Check if the filename meets the specified criteria
        if filename.endswith('out') and filename not in invalid_filenames and not filename.startswith('slurm'):
            # If criteria are met, add the filename to the list of valid filenames
            valid_filenames.append(filename)

    orca_filenames = []
    for filename in valid_filenames:
        if is_orca_output(root+'/'+filename):
            orca_filenames.append(filename)

    # Return the list of valid filenames
    return orca_filenames


def parse_file(file_path, data={}):
    """
    Parses a ORCA output file and extracts relevant numerical values.

    Args:
        file_path (str): The path to the file to be parsed.

    Returns:
        dict: A dictionary containing extracted numerical values from the file.

    Example:
        >>> file_path = 'your_file.txt'
        >>> result = parse_file(file_path)
        >>> print(result)
    """

    # Define regular expression patterns for each type of information
    temperature_pattern =         re.compile(r'Temperature\s+\.\.\.\s+([\d\.]+)\s+K')
    pressure_pattern =            re.compile(r'Pressure\s+\.\.\.\s+([\d\.]+)\s+atm')
    mass_pattern =                re.compile(r'Total Mass\s+\.\.\.\s+([\d\.]+)\s+AMU')
    gibbs_energy_pattern =        re.compile(r'Final Gibbs free energy\s+\.\.\.\s+([\d\.\-]+)\s+Eh')
    #enthalpy_pattern =            re.compile(r'Total enthalpy\s+\.\.\.\s+([\d\.\-]+)\s+Eh')
    inner_energy_pattern =        re.compile(r'Total correction\s+([\d\.\-]+)\s+Eh\s+([\d\.\-]+)\s+kcal/mol')
    entropy_correction_pattern =  re.compile(r'Total entropy correction\s+\.\.\.\s+([\d\.\-]+)\s+Eh\s+([\d\.\-]+)\s+kcal/mol')
    dipole_moment_pattern =       re.compile(r'Total Dipole Moment\s+:\s+([\d\.\-]+)\s+([\d\.\-]+)\s+([\d\.\-]+)')
    num_atoms_pattern =           re.compile(r'Number of atoms\s+\.\.\.\s+(\d+)')
    single_point_energy_pattern = re.compile(r'FINAL SINGLE POINT ENERGY\s+([\d\.\-]+)')
    #ge_el_pattern = re.compile(r'G-E\(el\)\s+\.\.\.\s+([\d\.]+)\s+Eh\s+([\d\.]+)\s+kcal/mol')
    ge_el_pattern =               re.compile(r'G-E\(el\)\s+\.\.\.\s+([\d\.\-]+)\s+Eh\s+([\d\.\-]+)\s+kcal/mol')
    zero_point_energy_pattern =   re.compile(r'Zero point energy\s+\.\.\.\s+([\d\.\-]+)\s+Eh\s+([\d\.\-]+)\s+kcal/mol')


    # Open the file and process each line
    with open(file_path, 'r') as file:
        for line in file:

            # Match each line against the defined patterns and extract values
            match_temperature = temperature_pattern.match(line)
            if match_temperature:
                data['Temperature'] = float(match_temperature.group(1))

            match_pressure = pressure_pattern.match(line)
            if match_pressure:
                data['Pressure'] = float(match_pressure.group(1))

            match_mass = mass_pattern.match(line)
            if match_mass:
                data['Total Mass'] = float(match_mass.group(1))

            match_single_point_energy = single_point_energy_pattern.match(line)
            if match_single_point_energy:
                data['Single Point Energy'] = float(match_single_point_energy.group(1)) * mc.EH2KJMOL


            match_gibbs_energy = gibbs_energy_pattern.match(line)
            if match_gibbs_energy:
                data['Final Gibbs Free Energy'] = float(match_gibbs_energy.group(1)) * mc.EH2KJMOL

            match_ge_el = ge_el_pattern.match(line)
            if match_ge_el:
                data['G-E(el) Energy'] = float(match_ge_el.group(1)) * mc.EH2KJMOL
                #data['G-E(el) kcal/mol'] = float(match_ge_el.group(2))

#           careful! Orca either includes the electronic energy or not, depending on availability. (see therm.out files for example)
#            match_enthalpy = enthalpy_pattern.match(line)
#            if match_enthalpy:
#                data['Total Enthalpy'] = float(match_enthalpy.group(1)) * mc.EH2KJMOL

            match_inner_energy = inner_energy_pattern.match(line)
            if match_inner_energy:
                inner_energy = float(match_inner_energy.group(1))
                kcal_per_mol = float(match_inner_energy.group(2))
                data['Inner Energy'] = float(inner_energy) * mc.EH2KJMOL
                #print(inner_energy)

            match_entropy_correction = entropy_correction_pattern.match(line)
            if match_entropy_correction:
                entropy_energy = float(match_entropy_correction.group(1))
                kcal_per_mol = float(match_entropy_correction.group(2))
                data['Entropy Correction'] = float(entropy_energy) * mc.EH2KJMOL

            match_dipole_moment = dipole_moment_pattern.match(line)
            if match_dipole_moment:
                dipole_values = [float(match_dipole_moment.group(i)) for i in range(1, 4)]
                data['Total Dipole Moment'] = dipole_values

            match_num_atoms = num_atoms_pattern.match(line)
            if match_num_atoms:
                data['Number of Atoms'] = int(match_num_atoms.group(1))

            match_zpe = zero_point_energy_pattern.search(line)
            if match_zpe:
                data['zpe'] = float(match_zpe.group(1))

    # Return the extracted data
    return data

def parse_scan_file(file_path, surface_data_with_indices=None):
    """
    Parses a ORCA output file and extracts surface scan data.

    Args:
        file_path (str): The path to the file to be parsed.

    Returns:
        dict: A dictionary containing extracted numerical values from the file.

    Example:
        >>> file_path = 'your_file.txt'
        >>> result = parse_file(file_path)
        >>> print(result)
    """

   
    # Define regular expression pattern for extracting scan energy data
    surface_data_pattern = re.compile(r'(?<=The Calculated Surface using the \'Actual Energy\'\n)(\s*\d+\.\d+\s+-?\d+\.\d+\s*\n)+')


    with open(file_path, 'r') as file:

        # Find matches in the text using the pattern
        match_surface_data = surface_data_pattern.search(file.read())
    
        if match_surface_data:
            # Extract the matched text and split it into lines
            surface_data_lines = match_surface_data.group(0).strip().split('\n')

            ## Extract values from each line and store them in a list of tuples
            #surface_data = [(float(line.split()[0]), float(line.split()[1])) for line in surface_data_lines]

            surface_data_with_indices = {}

            for i, line in enumerate(surface_data_lines):
                data = [float(coord) for coord in line.split()]
                #print(type(data))
                surface_data_with_indices[str(i)] = [data[0], data[1]*mc.EH2KJMOL]

    # Return the extracted data
    return surface_data_with_indices

def is_orca_output(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Check for specific indicators in the content
    indicators = [
        "* O   R   C   A *",
        "CARTESIAN COORDINATES (A.U.)",
        "FINAL SINGLE POINT ENERGY"
    ]
    
    return all(indicator in content for indicator in indicators)



def extract_orca_input(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    input_start = None
    input_end = None
    
    # Find the start and end of the input section
    for i, line in enumerate(lines):
        if "INPUT FILE" in line:
            input_start = i + 3
        if "****END OF INPUT****" in line:
            input_end = i + 1
            break
    #print(lines[input_start - 1])
    name_of_input = lines[input_start - 1].split('=')[1]

    # print( [line.lower() for line in lines[input_start:input_end]])

    # cut off "|  ?> " and convert to lower case
    return name_of_input, [line[5:].lower() for line in lines[input_start:input_end]]

def parse_orca_input(ser, input_file, files):
    """Look for keyword in input and return bool whether found or not"""
    ser['Geometry Optimization'] = False
    ser['Frequency Calculation'] = False
    xyz_input_coordinates_contained_in_output_file = False
    xyz_input_coordinates_file_name = False
    internal_input_coordinates_contained_in_output_file = False
    ser['Charge'] = False
    ser['Multiplicity'] = False
    ser['Potential Energy Surface Scan'] = False
    ser['Transition State Search'] = False
    start_of_coordinate_section = False
    end_of_coordinate_section = False
    for i, line in enumerate(input_file):

        # everything after # is a comment
        cut_line = line.split('#')[0]

        # remove left spaces
        cut_line = cut_line.lstrip()

        if cut_line.startswith('!') and not ser['Geometry Optimization']:
            ser['Geometry Optimization'] = "opt" in cut_line
        if cut_line.startswith('!') and not ser['Frequency Calculation']:
            ser['Frequency Calculation'] = "freq" in cut_line
        if cut_line.startswith('!') and not ser['Transition State Search']:
            ser['Transition State Optimization'] = "tsopt" in cut_line
        #if cut_line.startswith('!'): and not ser['Transition State Search']:
        #    ser['Transition State Search'] = "neb-ts" in cut_line
        if cut_line.startswith('*') and not xyz_input_coordinates_contained_in_output_file:
            xyz_input_coordinates_contained_in_output_file = cut_line.startswith('*xyz ')
        if cut_line.startswith('*xyzfile ') and not xyz_input_coordinates_file_name:
            xyz_input_coordinates_file_name = cut_line[1:].lstrip().split()[3]
        if cut_line.startswith('*') and not internal_input_coordinates_contained_in_output_file:
            internal_input_coordinates_contained_in_output_file = cut_line.startswith('*int ')
        if cut_line.startswith('*') and not ser['Charge'] and not ser['Multiplicity']:
            tmp = cut_line[1:].lstrip().split()
            ser['Charge'] = tmp[1]
            ser['Multiplicity'] = tmp[2]
        if cut_line.startswith('%geom scan'):
            ser['Potential Energy Surface Scan'] = False
        if (cut_line.startswith('end') or cut_line.startswith('*')) and not end_of_coordinate_section and start_of_coordinate_section:
            end_of_coordinate_section = i
        elif cut_line.startswith('*') and not start_of_coordinate_section:
            start_of_coordinate_section = i + 1

    if xyz_input_coordinates_contained_in_output_file:
        #print('indexes:', start_of_coordinate_section, end_of_coordinate_section)
        # print('RootFile: ', ser['RootFile'])
        #print(start_of_coordinate_section, end_of_coordinate_section)
        # print(input_file)
        # print(input_file[start_of_coordinate_section: end_of_coordinate_section])
        ser['Elements'], ser['xyz Input Coordinates'], ser['Number of Atoms'] = parse_orca_input_coordinates(input_file[start_of_coordinate_section: end_of_coordinate_section])
    elif xyz_input_coordinates_file_name:
        try:
            # Case insensitive reading, case sensitive filename
            ser['Number of Atoms'], _, ser['Elements'], ser['xyz Input Coordinates'] = common_functions.read_xyz(
                    ser['Root'] + '/' + next((filename for filename in files if filename.lower() == xyz_input_coordinates_file_name), None)
                    )
        except TypeError as e:
            print(f"{e}: xyz file not found in {ser['Root']}")
    elif internal_input_coordinates_contained_in_output_file:
        print('Internal Coordinates are not yet handeled')
        return
    else:
        raise ValueError

    try:
        if ser['xyz Input Coordinates'] and not (ser['Geometry Optimization'] or ser['Transition State Optimization']):
            ser['xyz Coordinates'] = ser['xyz Input Coordinates']
    except KeyError as e:
        print(f"{e} in ORCA coordinates handling")


    #if not ser['Elements']:
    #    raise ValueError
    #if not ser['xyz Coordinates']:
    #    raise ValueError

    return

def parse_orca_input_coordinates(lines):
    """
    Parses an ORCA input file to extract the elements, Cartesian coordinates, and the number of elements.

    Parameters:
    file_path (str): Path to the ORCA input file.

    Returns:
    tuple: A tuple containing:
        - elements (list of str): The list of element symbols.
        - coordinates (list of list of float): The Nx3 list of coordinates.
        - num_elements (int): The number of elements.
    """

    elements = []
    coordinates = []

    #print(lines)
    for line in lines:
        # print(line)
        parts = line.split()
        if len(parts) == 4:  # Ensure the line has exactly 4 parts (element and 3 coordinates)
            elements.append(parts[0])
            coordinates.append([float(parts[1]), float(parts[2]), float(parts[3])])
        else:
            #print('line =', line)
            raise KeyError # wrong index 

    num_elements = len(elements)

    return elements, coordinates, num_elements

def further_input_parsing(file_content):
    #extracts string with elements, coordinates, and number of atoms
    #lines = file_content.split('\n')
    start_line = None
    end_line = None
    #print(file_content)

    for i, line in enumerate(file_content):
        if '*' in line:
            #print(line)
            if start_line is None:
                start_line = i
            else:
                end_line = i
                break

    return end_line - start_line - 1

def extract_last_vibrational_frequencies(file_path, degrees_of_freedom):
    with open(file_path, 'r') as file:
        orca_output = file.readlines()

    frequency_lines = [line for line in orca_output if 'cm**-1' in line]

    frequencies = []
    for line in frequency_lines:
        parts = line.split()
        try:
            freq = float(parts[1])
            frequencies.append(freq)
        except ValueError:
            continue
    # This happens for TS-Optimizations
    if len(frequencies) % degrees_of_freedom != 0:
        raise ValueError
    # This happens for TS-Optimizations
    if len(frequencies) > degrees_of_freedom:
        frequencies = frequencies[-degrees_of_freedom:]
        #print(frequencies[-degrees_of_freedom:])
    if len(frequencies) % degrees_of_freedom != 0:
        print('error in some frequency file')
        raise ValueError
    #print('Frequencies:', frequencies)
    frequencies.sort()
    return frequencies


    #print ([float(freq) for freq in last_frequencies])
    return [float(freq) for freq in last_frequencies]
