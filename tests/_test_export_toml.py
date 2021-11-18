import pytest
from tomlkit import document, loads

from hand.config.export_toml import (
    _ERR_NON_VAILD_DEFAULT_CFG,
    Config,
    add_commented_section,
    export_default_config,
)


@pytest.mark.unit
def test_create_config_toml_success():
    _: str = export_default_config()


@pytest.mark.unit
@pytest.mark.incremental
class TestWouldExportRightFormat:
    def test_toml_and_pydantic_keys_must_conform(self):

        toml_docu = loads(export_default_config())
        pydantic_config = Config.get_default()

        # first level name
        assert set(toml_docu.keys()) == set(pydantic_config.dict().keys())

        # second level name
        for toml_section_name, toml_dic in toml_docu.items():
            pydantic_dic = getattr(pydantic_config, toml_section_name)
            assert toml_dic.keys() == pydantic_dic.dict().keys()

    def test_exported_default_config_must(self):
        _: Config = Config(**loads(export_default_config()))


@pytest.mark.unit
@pytest.mark.incremental
class TestBuildToml:
    def test_commented_section_dict_must_have_comment(self):
        docu = document()
        with pytest.raises(_ERR_NON_VAILD_DEFAULT_CFG):
            add_commented_section(
                docu=docu, section_name="test", dic={"t2": {"value": "default"}},
            )

    def test_commented_section_dict_must_have_value(self):
        docu = document()
        with pytest.raises(_ERR_NON_VAILD_DEFAULT_CFG):
            add_commented_section(
                docu=docu, section_name="test", dic={"t2": {"comment": "default"}},
            )

    def test_valid_section(self):
        docu = document()
        add_commented_section(
            docu=docu,
            section_name="test",
            dic={"t1": "val1", "t2": {"comment": "comment1", "value": "default"}},
        )
