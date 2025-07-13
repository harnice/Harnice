import yaml
from harnice import fileio

def load():
    """
    Loads and returns the contents of the ESCH YAML file.
    
    Returns:
        dict: Parsed YAML data.
    """
    yaml_path = fileio.path("harness yaml")
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)