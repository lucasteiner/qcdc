#!/usr/bin/env python3
import os
import pandas as pd

import common_functions
import my_constants as mc
from parse_args import get_arguments
from parse_orca_calculation import parse_orca
from parse_turbomole_calculation import parse_turbomole
from parse_censo_calculation import parse_censo

def ignore_dirs_by_name(top, ignore_names):
    """
    Walks through the directory tree from the top, ignoring directories with specified names.
    
    :param top: The top-level directory to start walking from.
    :param ignore_names: A set of directory names to ignore.
    """
    for root, dirs, files in os.walk(top):
        dirs[:] = [d for d in dirs if d not in ignore_names]
        yield root, dirs, files

def ignore_dirs_containing(walk, substring):
    """
    Walks through the directory tree from the top, ignoring directories containing a specific substring.
    
    :param top: The top-level directory to start walking from.
    :param substring: The substring to look for in directory names to ignore.
    """
    for root, dirs, files in walk:
        dirs[:] = [d for d in dirs if substring not in d]
        yield root, dirs, files

def main():
    """
    Walks through directories and files, and calls the parsers (orca and turbomole).
    """
    df = []  # Initialize an empty list to collect dataframes
    if not os.path.exists(mc.XYZDIR):
        os.makedirs(mc.XYZDIR)

    # Ignore folders in os.walk

    ignore_folders = []
    try:
        with open(args.ignore_folders, 'r') as file:
            ignore_folders = file.readlines()
            ignore_folders = [line.strip('\n') for line in ignore_folders]
            ignore_folders = [line.strip('/') for line in ignore_folders]
    except FileNotFoundError:
        print(f"The file at {args.ignore_folders} does not exist.")
    ignore_folders.append(['./xyz', './__pycache__', './.venv', './.git'])
    print(f"Ignoring directories with the names: \n {ignore_folders}")

    my_walk = ignore_dirs_by_name(os.path.curdir, ignore_folders)

    #unwanted_substrings = ['CONF']
    #for substring in unwanted_substrings:
    #    my_walk = ignore_dirs_containing(my_walk, substring)

    #for root, dirs, files in os.walk(os.path.curdir, ignore_folders):
    for root, dirs, files in my_walk:
        # Exclude specific folders
        # if root.startswith('./xyz') or root.startswith('./__pycache__') or root.startswith('./.venv') or root.startswith('./.git'):
        #     continue

        #new_cycle = False
        #for folder in ignore_folders:
        #    if root.startswith(folder):
        #        new_cycle = True 
        #if new_cycle:
        #    continue


        # Parse ORCA calculations
        combined = []
        print('Root: ', root)
        if args.orca:
            orca_calculations = parse_orca(root, dirs, files)
            if orca_calculations:
                combined.extend(orca_calculations)

        # Parse TURBOMOLE calculations
        if args.turbomole:
            ser = parse_turbomole(root, dirs, files)
            if ser:
                combined.append(ser)

        # Parse CENSO calculations
        if args.censo:
            ser = parse_censo(root, dirs, files)
            if ser:
                combined.append(ser)


        # Post-processing for all calculations of a folder
        if combined:
            for calculation in combined:
                # If frequencies are present, coordinates should also be present
                if calculation.get('Frequency Calculation'):
                    try:
                        common_functions.derive_data(
                            calculation,
                            calculation['Elements'],
                            calculation['xyz Coordinates'],
                            calculation['Frequencies']
                        )
                    except KeyError as e:
                        print(f"{e} in derive_data. Some data not found")
                        pass

                if calculation.get('Single Point Energy'):
                    try:
                        info_string = common_functions.format_properties(
                            charge=calculation.get('Charge'),
                            s2=calculation.get('S2'),
                            dipole=calculation.get('Dipole Moment'),
                            vibration=calculation.get('Frequencies'),
                            zpe=calculation.get('Zero Point Energy')
                        )
                        common_functions.write_xyz(
                            calculation['Elements'],
                            calculation['xyz Coordinates'],
                            calculation['xyz File Name'],
                            comment=calculation['Single Point Energy']/mc.EH2KJMOL,
                            bottom_info=''
                        )
                        # t2energy: prints also vibrations, but not easily readable by other scripts
                        #common_functions.write_xyz(
                        #    calculation['Elements'],
                        #    calculation['xyz Coordinates'],
                        #    calculation['xyz File Name'],
                        #    comment="Generated by script",
                        #    bottom_info=info_string
                        #)
                    except KeyError as e:
                        print(f"{e} in write_xyz. Some data not found")
                        pass
                    # Extract the number in the /CONF string which is used in censo calculations.
                    calculation['Censo Conformer Number'] = common_functions.extract_conf_number(calculation.get('Root'))

            # Append the cleaned and calculated data of the folder
            df.extend(combined)

    # Final part
    df = pd.DataFrame(df)
    if not args.savexyz:
        df.drop('xyz Coordinates', axis=1, errors='ignore')
        df.drop('Frequencies', axis=1, errors='ignore')
        df.drop('Elements', axis=1, errors='ignore')
    df.to_json('data.json')

    return df


if __name__ == '__main__':
    args = get_arguments()
    df = main()
    print(df)
    print(df.keys())
    print(df.info())
