import sys
from typing import List, Tuple

import requests
import typer
from halo import Halo

from ..config.github import config_add_students
from ..core.color_text import normal, warn
from ..ensures import ensure_gh_token
from ..shared_options import opt_dry, opt_gh_org, opt_github_token
from ..utils.github_entities import Team
from ..utils.github_scanner import github_headers


def print_table(data, cols=5, wide=15, indent=2):
    """Prints formatted data on columns of given width."""
    n, r = divmod(len(data), cols)
    pat = "{{:{}}}".format(wide)
    line = "\n{}".format(" " * indent).join(pat * cols for _ in range(n))

    # indent the first line
    line = " " * indent + line

    last_line = " " * indent + pat * r
    print(line.format(*data))
    print(last_line.format(*data[n * cols :]))


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
        metavar="✏️ student_handles✏️",
        default=...,
        help="list of student handles separated by white space",
    ),
    github_team: str = typer.Option(
        config_add_students["default_team_slug"],
        "--team",
        help="invite to the specfic team under organization",
    ),
    dry: bool = opt_dry,
    github_token: str = opt_github_token,
    github_organization: str = opt_gh_org,
):
    """
    invite students to join our Github organization
    """
    safety = SafetyActor(dry=dry)
    safety.ensure_gh_token(github_token)

    # TODO: use logging lib to log messages
    spinner = Halo(stream=sys.stderr)
    if dry:
        spinner.info("Dry run")

    spinner.info("fetch existing team members from GitHub")
    team = Team(
        dry=dry,
        org=github_organization,
        team_slug=github_team,
        github_token=github_token,
    )
    num_member = len(team.members.keys())
    words = (
        normal.txt("target team: ")
        .kw(f"{github_team}")
        .txt("( ")
        .kw2(num_member)
        .txt(" members) ")
    )
    spinner.succeed(words.to_str())

    existed_members = set(team.members.keys())
    outside_users = list(set(github_students) - existed_members)
    spinner.info("Check valid Github users")
    invalid_handles = invalid_user_handles(
        outside_users, github_token=github_token, safety=safety, spinner=spinner
    )

    if len(invalid_handles) != 0:
        print("non-existed github user handles:")
        # control strings take space
        print_table([warn.txt(i).to_str() for i in invalid_handles], cols=5, wide=25)
    non_member_valid_users = list(set(outside_users) - set(invalid_handles))

    # membership info
    spinner.info("Check Membership information")
    users_in_pending, users_to_invite = find_outside_members(
        non_member_valid_users, spinner=spinner, team=team, dry=dry
    )

    if len(users_in_pending) > 0:
        print(f"Users already in pending state (total:{len(users_in_pending)}):")
        print_table(users_in_pending)

    print(f"Users to add (total:{len(users_to_invite)})")
    print_table(users_to_invite)
    print("-" * 30)

    spinner.info("start to invite users")
    success_user, failed_users = invite_user_to_team(
        team=team, users=users_to_invite, spinner=spinner
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


def find_outside_members(
    user_handles: List[str], spinner, team: Team, dry: bool = False
) -> Tuple[List[str], List[str]]:
    """return two type of members,
        1. have invited but still in pending state
        2. not invited, not-organization users
        """
    pending_users, outside_users = [], []
    total = len(user_handles)
    for idx, username in enumerate(user_handles, start=1):
        skip = "" if not dry else "[skip]: "
        spinner.start(f"{skip}{idx}/{total}: {username}")
        res = team.get_memberships(username)
        if res.status_code == 200:
            state = res.json()["state"]
            if state == "pending":
                pending_users.append(username)
            elif state == "unknown":
                outside_users.append(username)
    return pending_users, outside_users


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
