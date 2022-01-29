from typing import List
from unittest.mock import MagicMock

import iso8601
import pytest
from attr import attrib, attrs

from hand.exchange import GitHubCommitInfo, GitHubRepoCommit
from hand.scripts.times import (
    DeadLinePassed,
    ScriptTimes,
    ScriptTimesDisplay,
    ScriptTimesDisplayImpl,
)


@pytest.mark.api
def test_api_get_commit():
    from hand.api.github import GithubAPI
    from hand.config import settings

    gh = GithubAPI(token=settings.github.token, org=settings.github.org)
    target = GitHubRepoCommit(name="hw1-ianre657", commit_hash="4871d8afd")
    push_time = gh.get_commit_pushed_time(target)
    assert push_time is not None
    print(f"\n push time of commit:{target} -> {push_time}")


@attrs(auto_attribs=True)
class TimeAnswer:
    input: GitHubRepoCommit
    expected: GitHubCommitInfo

    @classmethod
    def mk(cls, repo: str, hash: str, pushtime: str) -> "TimeAnswer":
        c = GitHubRepoCommit(name=repo, commit_hash=hash)
        i = GitHubCommitInfo(commit_hash=hash, pushed_time=pushtime, msg="", repo=repo)
        return TimeAnswer(input=c, expected=i)


@attrs(auto_attribs=True)
class FakeDisplay(ScriptTimesDisplay):
    passed: List[DeadLinePassed] = attrib(factory=list)

    def add_result_dlpassed(self, p: DeadLinePassed):
        self.passed.append(p)


def test_display():
    deadline = "2019-11-11 23:59:59"
    input_commits = [
        "2019-11-10 23:59:59",
        "2019-11-11 22:59:59",
        "2019-11-12 13:00:11",
        "2019-11-13 20:59:59",
    ]

    class MockedGHAPI:
        def __init__(self):
            m = MagicMock()
            m.side_effect = input_commits
            self.get_commit_pushed_time = m

    gh_api = MockedGHAPI()
    display = ScriptTimesDisplayImpl(deadline=deadline)
    script = ScriptTimes(
        gh_api=gh_api,
        repos=[
            GitHubRepoCommit(name=f"repo{n}", commit_hash=f"aaaaaa{n}")
            for n in range(4)
        ],
        deadline=iso8601.parse_date(deadline),
        display=display,
    )
    script.run()


def test_times():
    deadline = "2019-11-11 23:59:59"
    input_commits = [
        "2019-11-10 23:59:59",
        "2019-11-11 22:59:59",
        "2019-11-12 13:00:11",
        "2019-11-13 20:59:59",
    ]

    class MockedGHAPI:
        def __init__(self):
            m = MagicMock()
            m.side_effect = input_commits
            self.get_commit_pushed_time = m

    gh_api = MockedGHAPI()
    display = FakeDisplay()
    script = ScriptTimes(
        gh_api=gh_api,
        repos=[
            GitHubRepoCommit(name=f"repo{n}", commit_hash=f"aaaaaa{n}")
            for n in range(4)
        ],
        deadline=iso8601.parse_date(deadline),
        display=display,
    )
    script.run()

    assert len(display.passed) == 2
    gh_api.get_commit_pushed_time.assert_called()
