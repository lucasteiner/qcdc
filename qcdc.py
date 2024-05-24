#!/usr/bin/env python3
import os
import pandas as pd

import common_functions
import my_constants as mc
from parse_args import get_arguments
from parse_orca_calculation import parse_orca
from parse_turbomole_calculation import parse_turbomole


def main():
    """
    Walks through directories and files, and calls the parsers (orca and turbomole).
    """
    df = []  # Initialize an empty list to collect dataframes
    if not os.path.exists(mc.XYZDIR):
        os.makedirs(mc.XYZDIR)

    for root, dirs, files in os.walk(os.path.curdir):

        # Exclude specific folders
        if root.startswith('./xyz') or root.startswith('./__pycache__') or root.startswith('./.venv'):
            continue

        # Parse ORCA calculations
        combined = []
        if args.orca:
            orca_calculations = parse_orca(root, dirs, files)
            if orca_calculations:
                combined.extend(orca_calculations)

        # Parse TURBOMOLE calculations
        if args.turbomole:
            ser = parse_turbomole(root, dirs, files)
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

                try:
                    info_string = common_functions.format_properties(
                        charge=calculation.get('Charge'),
                        s2=calculation.get('S2'),
                        dipole=calculation.get('Dipole Moment'),
                        vibration=calculation.get('frequencies'),
                        zpe=calculation.get('Zero Point Energy')
                    )
                    common_functions.write_xyz(
                        calculation['Elements'],
                        calculation['xyz Coordinates'],
                        calculation['xyz File Name'],
                        comment="Generated by script",
                        bottom_info=info_string
                    )
                except KeyError as e:
                    print(f"{e} in write_xyz. Some data not found")
                    pass
                # Extract the number in the /CONF string which is used in censo calculations.
                calculation['Censo Conformer Number'] = common_functions.extract_conf_number(calculation.get('Root'))

            # Append the cleaned and calculated data of the folder
            df.extend(combined)

    return pd.DataFrame(df)


if __name__ == '__main__':
    args = get_arguments()
    df = main()
    df.to_json('data.json')
    print(df)
    print(df.keys())
    print(df.info())
