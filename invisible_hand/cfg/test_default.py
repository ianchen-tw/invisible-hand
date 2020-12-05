import pytest
from tomlkit import document

from .default import *
from .default import _ERR_NON_VAILD_DEFAULT_CFG


@pytest.mark.unit
def test_valid_section():
    docu = document()
    add_commented_section(
        docu=docu,
        section_name="test",
        dic={"t1": "val1", "t2": {"comment": "comment1", "value": "default"}},
    )


@pytest.mark.unit
def test_commented_section_dict_must_have_comment():
    docu = document()
    with pytest.raises(_ERR_NON_VAILD_DEFAULT_CFG):
        add_commented_section(
            docu=docu, section_name="test", dic={"t2": {"value": "default"}},
        )


@pytest.mark.unit
def test_commented_section_dict_must_have_value():
    docu = document()
    with pytest.raises(_ERR_NON_VAILD_DEFAULT_CFG):
        add_commented_section(
            docu=docu, section_name="test", dic={"t2": {"comment": "default"}},
        )


@pytest.mark.unit
def test_create_config_success():
    _ = create_default_config()
