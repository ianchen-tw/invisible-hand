import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from hand.cli.check import DoCheck
from hand.config import HandConfig


def namespace_from_dic(dic):
    return json.loads(json.dumps(dic), object_hook=lambda item: SimpleNamespace(**item))


def test_namespace_conversion():
    dic = {"a": {"b": "c"}, "d": "e"}
    res = namespace_from_dic(dic)
    assert res.a.b == "c"
    assert res.d == "e"


class ConfigForTest:
    def __init__(self):
        self.github = HandConfig.Github(token="test-token", org="test-org")
        self.google_spreadsheet = HandConfig.Google(
            url="google-url", cred_filename="somename"
        )
        self.crawl = HandConfig.CrawlClassroom(
            gh_login="test-login", classroom_id="classroom-id-test",
        )
        self.grant = HandConfig.GrantReadAccess(reader_team="team-test")
        self.add = HandConfig.AddStudens(student_team="team-student-test")
        self.times = HandConfig.EventTimes(compare_deadline="2066-6-6")
        self.announce = HandConfig.AnnounceGrade(feedback_src_repo="test-fb-repo")


@pytest.fixture
def default_setting() -> HandConfig:
    return HandConfig.from_orm(ConfigForTest())


def test_docheck_should_ask_git(default_setting: HandConfig):

    check = DoCheck(default_setting).withOptions(gh_config_valid=True)

    check.gh_api.can_access_org = MagicMock(return_value=True)
    assert check.run().success == True

    check.gh_api.can_access_org = MagicMock(return_value=False)
    assert check.run().success == False
