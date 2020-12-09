import shutil
from pathlib import Path

import attr
from tomlkit import parse

from .base_config import Config
from .export_toml import export_default_config
from .words import STR_CFG_NOT_EXISTS

DEFAULT_BASE_FOLDER = Path.home() / ".invisible-hand"
CFG_FILENAME = "config.toml"

# TODO: dectect corrupted/uncorrect-formatted Config


class CONFIG_NOT_EXISTS(Exception):
    def __init__(self, path):
        self.path = path
        super().__init__(self)

    def __str__(self):
        return f"{STR_CFG_NOT_EXISTS}: {self.path}"


class CONFIG_CORRUPTED(Exception):
    pass


@attr.s(auto_attribs=True)
class ConfigManager:
    base_folder: Path = attr.ib(default=DEFAULT_BASE_FOLDER, converter=Path)
    config_path: Path = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.config_path = self.base_folder / CFG_FILENAME
        self.base_folder.mkdir(parents=True, exist_ok=True)

    def create_default(self):
        with open(self.config_path, "w") as f:
            f.write(export_default_config())

    def read_config(self) -> Config:
        """ Read config file
            raise `CONFIG_NOT_EXISTS` if file not exists
        """
        if not self.config_path.exists():
            raise CONFIG_NOT_EXISTS(self.config_path)
        with open(self.config_path, "r") as f:
            cfg_toml = parse(f.read())
            return Config(**cfg_toml)

    def remove(self):
        if self.base_folder.exists:
            shutil.rmtree(self.base_folder)

    def get_base_path(self) -> Path:
        return self.base_folder
