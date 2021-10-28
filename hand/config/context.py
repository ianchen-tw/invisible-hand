from typing import Optional

from pydantic import BaseModel

from .config_manager import Config, ConfigManager


class AppContext(BaseModel):
    config_manager: ConfigManager = ConfigManager()
    config: Optional[Config] = None

    class Config:
        arbitrary_types_allowed = True


app_context = AppContext()
