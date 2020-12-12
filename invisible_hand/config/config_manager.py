import shutil
from pathlib import Path
from typing import Union

import attr
from tomlkit import parse

from .base_config import Config
from .export_toml import export_default_config
from .words import STR_CFG_NOT_EXISTS

DEFAULT_BASE_FOLDER = Path.home() / ".invisible-hand"
CFG_FILENAME = "config.toml"
CLIENT_SECRET_FILENAME = "client_secret.json"


class CONFIG_NOT_EXISTS(Exception):
    def __init__(self, path):
        self.path = path
        super().__init__(self)

    def __str__(self):
        return f"{STR_CFG_NOT_EXISTS}: {self.path}"


@attr.s(auto_attribs=True)
class ConfigManager:
    base_folder: Path = attr.ib(default=DEFAULT_BASE_FOLDER, converter=Path)
    config_path: Path = attr.ib(init=False)
    google_client_secret_path: Path = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.change_base_folder(self.base_folder)

    def change_base_folder(self, new_base: Union[Path, str]):
        self.base_folder = Path(new_base)
        self.config_path = self.base_folder / CFG_FILENAME
        self.google_client_secret_path = self.base_folder / CLIENT_SECRET_FILENAME

    def _ensure_base_folder(self):
        """Create base folder if not exists"""
        self.base_folder.mkdir(parents=True, exist_ok=True)

    def create_default(self):
        self._ensure_base_folder()
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
