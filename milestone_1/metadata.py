import yaml
import os

CONFIG_PATH = "config/role_mapping.yaml"

def load_role_mapping(config_path: str = CONFIG_PATH) -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def infer_department(file_path: str, role_config: dict) -> str:
    file_path = file_path.replace("\\", "/").lower()

    for department, config in role_config["roles"].items():
        for folder in config["folders"]:
            if folder.lower() in file_path:
                return department

    return "Unknown"

def get_allowed_roles(department: str, role_config: dict) -> list:
    return role_config["roles"].get(department, {}).get("allowed_roles", [])