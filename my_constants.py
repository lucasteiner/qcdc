import yaml
import os

# Get the absolute path of the yaml file
yaml_file_path = os.path.dirname(os.path.abspath(__file__)) + '/config.yml'
current_file_path = 'config.yml'
#print(current_file_path)

# Function to import variables from YAML into a Python dictionary
def import_yaml_variables(yaml_path):
    with open(yaml_path, 'r') as file:
        data = yaml.safe_load(file)
    return data

# Retrieve the variables
if os.path.exists(current_file_path):
    print('config exists here')
    print(current_file_path)
    yaml_variables = import_yaml_variables(current_file_path)
elif not os.path.exists(current_file_path):
    print('config does not exist, using default')
    print(yaml_file_path)
    yaml_variables = import_yaml_variables(yaml_file_path)
else:
    print(f"Error while reading the YAML file")
    print(current_file_path)
    raise FileNotFoundError


# Import the variables into the current namespace
for key, value in yaml_variables.items():
    globals()[key] = value

# Optional: Print variables for verification
if __name__ == '__main__':
    print("Variables imported from YAML:")
    for key, value in yaml_variables.items():
        print(f"{key}: {value}")

