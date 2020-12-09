import pytest

from .base_config import *


@pytest.mark.unit
def test_generate_config_pydantic_success():
    _: Config = Config.get_default()
