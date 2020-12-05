from pathlib import Path
import shutil

from .default import create_default_config

base_folder = Path.home() / ".config" / "invisible-hand"
config_file = base_folder / "config.yaml"


class ConfigManager:
    def __init__(self):
        base_folder.mkdir(parents=True, exist_ok=True)
        print(f"create {base_folder}")

    def create_default(self):
        with open(config_file, "w") as f:
            f.write(create_default_config())

    def remove(self):
        if base_folder.exists:
            shutil.rmtree(base_folder)
