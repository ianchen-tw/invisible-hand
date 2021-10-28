import pytest

from hand.config.base_config import Config


@pytest.mark.unit
def test_generate_config_pydantic_success():
    _: Config = Config.get_default()
