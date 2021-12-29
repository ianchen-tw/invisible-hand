from unittest.mock import MagicMock, call

from hand.scripts.add import ScriptAddStudents, unique


def test_unique():
    assert unique([1, 1, 2, 2, 2, 3]) == [1, 2, 3]


class FakeGithubAPI:
    def __init__(self):
        self.invite_user_to_team = MagicMock(return_value=True)


def test_add_student():
    fake_gh_api = FakeGithubAPI()
    team = "test_team"
    user_handles = ["a@gmail.com", "a", "bb", "sead"]
    script = ScriptAddStudents(
        gh_invite_team=team,
        user_handles=user_handles,
        dry_run=False,
        gh_api=fake_gh_api,
    )
    script.run()

    expected_calls = [
        call(team_slug="test_team", user="a"),
        call(team_slug="test_team", user="a@gmail.com"),
        call(team_slug="test_team", user="sead"),
        call(team_slug="test_team", user="bb"),
    ]
    fake_gh_api.invite_user_to_team.assert_has_calls(expected_calls, any_order=True)


def test_dry_run_should_not_call_api():
    fake_gh_api = FakeGithubAPI()
    team = "test_team"
    user_handles = ["a@gmail.com", "a", "bb", "sead"]
    script = ScriptAddStudents(
        gh_invite_team=team,
        user_handles=user_handles,
        dry_run=True,
        gh_api=fake_gh_api,
    )
    script.run()

    fake_gh_api.invite_user_to_team.assert_not_called()
