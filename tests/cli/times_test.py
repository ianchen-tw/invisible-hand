import iso8601
import pytest

from hand.cli.cmd.times import (
    ParseError,
    _get_possible_time_formats,
    _parse_commit_from_text,
)
from hand.exchange import GitHubRepoCommit


def test_possible_formats():
    for t in _get_possible_time_formats():
        iso8601.parse_date(t)


def test_parse_must_accept_correct_data():
    commit = _parse_commit_from_text("repo1:aaa repo2:bbb")
    assert GitHubRepoCommit(name="repo1", commit_hash="aaa") == commit[0]
    assert GitHubRepoCommit(name="repo2", commit_hash="bbb") == commit[1]


def test_parse_multi_line_data():
    mline_input = """
    r1:aaa r2:bbb
    r3:2a3 r4:aasd3 r5:55
    """
    commits = _parse_commit_from_text(mline_input)
    assert len(commits) == 5


def test_parse_must_reject_no_field():
    with pytest.raises(ParseError):
        _parse_commit_from_text("repo1-aaa repo2:bbb")
    with pytest.raises(ParseError):
        _parse_commit_from_text("repo1aaa")
