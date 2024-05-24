import yaml

# Path to the uploaded YAML file
yaml_file_path = 'config.yml'

# Function to import variables from YAML into a Python dictionary
def import_yaml_variables(yaml_path):
    try:
        with open(yaml_path, 'r') as file:
            data = yaml.safe_load(file)
        return data
    except Exception as e:
        print(f"Error while reading the YAML file: {e}")
        return {}

# Retrieve the variables
yaml_variables = import_yaml_variables(yaml_file_path)

# Import the variables into the current namespace
for key, value in yaml_variables.items():
    globals()[key] = value

# Optional: Print variables for verification
if __name__ == '__main__':
    print("Variables imported from YAML:")
    for key, value in yaml_variables.items():
        print(f"{key}: {value}")

