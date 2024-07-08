# parse_args.py
import argparse

def on_off_type(value):
    """Parses 'on'/'off' strings into a boolean value."""
    value = value.lower()
    if value == 'on':
        return True
    elif value == 'off':
        return False
    else:
        raise argparse.ArgumentTypeError("Accepted values are 'on' or 'off'.")

def get_arguments():
    """
    Parses command-line arguments for --orca, --turbomole, and --censo.
    Defaults to True but can be explicitly set with 'on'/'off'.
    """
    parser = argparse.ArgumentParser(description='Process boolean arguments with on/off control.')

    # Add arguments with custom 'on_off_type'
    parser.add_argument('--orca', type=on_off_type, default=True, help="Control ORCA (default: on).")
    parser.add_argument('--turbomole', type=on_off_type, default=True, help="Control TURBOMOLE (default: on).")
    parser.add_argument('--censo', type=on_off_type, default=True, help="Control CENSO (default: on).")
    parser.add_argument('--savexyz', type=on_off_type, default=False, help="Save xyz data in dataframe in addition to folders (default: off).")
    parser.add_argument('--ignore_folders', type=str, default='ignore_folders', help="File with Foldernames to be ignored. (default: ignore_folders, set by 'ls -d ./*/ > ignore_folders')")

    # Parse and return the arguments
    return parser.parse_args()

# Optional: Testing directly if executed as a standalone script
if __name__ == '__main__':
    args = get_arguments()
    print(f"Orca: {args.orca}")
    print(f"Turbomole: {args.turbomole}")
    print(f"Censo: {args.censo}")
    print(f"saveXYZ: {args.savexyz}")
