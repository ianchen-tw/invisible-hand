import sys
from typing import List, Optional, Tuple

import requests
import typer
from halo import Halo
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel

from invisible_hand.config import app_context
from ..ensures import ensure_config_exists, ensure_gh_token
from ..utils.github_entities import Team
from ..utils.github_scanner import github_headers
from .shared_options import opt_all_yes, opt_dry, opt_gh_org, opt_github_token


def print_table(data):
    """Prints formatted data in columns"""
    users = [Panel(user, expand=True) for user in data]
    columns = Columns(users, equal=True)
    Console().print(columns)


# Use a "team slug"
# for example: "2019 Students-hello" -> "2019_students-hello"


def check_is_github_user(github_id, github_token) -> bool:
    res = requests.get(
        f"https://api.github.com/users/{github_id}", headers=github_headers(github_token),
    )
    return res.status_code == 200


class SafetyActor:
    """ Rexport functions to respect dry run option.
    Which would not make the actual call if `dry==true`
    """

    def __init__(self, dry: bool):
        self._dry = dry

    def _safe_trigger(self, func, *args, **kwargs):
        __tracebackhide__ = True
        triggered, val = False, None
        if not self._dry:
            val = func(*args, **kwargs)
            triggered = True
        else:
            pass
            # typer.echo("safe enabled, not fire ")
        return triggered, val

    def ensure_gh_token(self, token: str):
        triggered, val = self._safe_trigger(ensure_gh_token, token=token)
        return val if triggered else True

    def is_github_user(self, github_id: str, github_token: str) -> bool:
        def is_gh_user(gh_id: str, token: str) -> bool:
            res = requests.get(
                f"https://api.github.com/users/{gh_id}", headers=github_headers(token),
            )
            return res.status_code == 200

        triggered, val = self._safe_trigger(
            is_gh_user, gh_id=github_id, token=github_token
        )
        return val if triggered else True


def add_students(
    github_students: List[str] = typer.Argument(
        metavar="student_handles",
        default=...,
        help="list of student handles separated by white space",
    ),
    github_team: Optional[str] = typer.Option(
        None, "--team", help="invite to the specfic team under organization",
    ),
    yes: bool = opt_all_yes,
    dry: bool = opt_dry,
    github_token: Optional[str] = opt_github_token,
    github_organization: Optional[str] = opt_gh_org,
):
    """
    Invite students to join our Github organization
    """
    ensure_config_exists()

    def fallback(val, fallback_value):
        return val if val else fallback_value

    # Handle default value manually because we'll change our config after app starts up
    github_token: str = fallback(
        github_token, app_context.config.github.personal_access_token
    )
    github_organization: str = fallback(
        github_organization, app_context.config.github.organization
    )
    github_team: str = fallback(
        github_team, app_context.config.add_students.default_team_slug
    )

    safety = SafetyActor(dry=dry)
    safety.ensure_gh_token(github_token)

    # TODO: use logging lib to log messages
    spinner = Halo(stream=sys.stderr)
    if dry:
        spinner.info("Dry run")

    if not (
        yes or typer.confirm(f"Add students to {github_organization}/{github_team}?")
    ):
        raise typer.Abort()

    spinner.info("fetch existing team members from GitHub")
    team = Team(
        dry=dry,
        org=github_organization,
        team_slug=github_team,
        github_token=github_token,
    )
    num_member = len(team.members.keys())

    spinner.succeed(f" target team: {github_team} ({num_member} members) ")

    existed_members = set(team.members.keys())
    outside_users = list(set(github_students) - existed_members)
    spinner.info("Check valid Github users")
    invalid_handles = invalid_user_handles(
        outside_users, github_token=github_token, safety=safety, spinner=spinner
    )

    if len(invalid_handles) != 0:
        print("non-existed github user handles:")
        # control strings take space
        print_table(invalid_handles)
    non_member_valid_users = list(set(outside_users) - set(invalid_handles))

    print(f"Users to add (total:{len(non_member_valid_users)})")
    print_table(non_member_valid_users)
    print("-" * 30)

    spinner.info("start to invite users")
    success_user, failed_users = invite_user_to_team(
        team=team, users=non_member_valid_users, spinner=spinner
    )
    if len(failed_users) > 0:
        print("Users failed to add")
        print_table(failed_users)

    spinner.succeed("Add students successfully")


def invalid_user_handles(
    to_verify: List[str], github_token: str, safety: SafetyActor, spinner
) -> List[str]:
    """ return list of non-valid github user handles
        """
    invalid = []
    spinner.start()
    total = len(to_verify)
    for idx, user_name in enumerate(to_verify, start=1):
        text = f"{idx}/{total} Check valid GitHub username : {user_name}"
        if safety.is_github_user(user_name, github_token):
            spinner.succeed(text)
        else:
            invalid.append(user_name)
            spinner.fail(text)
    return invalid

def invite_user_to_team(
    team: Team, users: List[str], spinner
) -> Tuple[List[str], List[str]]:
    """ invite user to team and return results in different name list
        """
    # make users unique
    users = list(set(users))
    success, failed, = [], []
    for user_name in users:
        res = team.add_user_to_team(user_name=user_name)
        if res.status_code == 200:
            success.append(user_name)
            spinner.succeed(f"add user: {user_name}")
        else:
            failed.append(user_name)
            spinner.fail(f"failed to add user: {user_name}")
    return success, failed
