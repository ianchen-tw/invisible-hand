import sys

import click
import requests
from halo import Halo

from ..config.github import config_add_students, config_github
from ..core.color_text import normal, warn
from ..ensures import ensure_gh_token
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


@click.command()
@click.argument("student_handles", nargs=-1)
@click.option(
    "--dry",
    help="dry run, do not fire final request to remote",
    is_flag=True,
    default=False,
)
@click.option(
    "--token", default=config_github["personal_access_token"], help="github access token"
)
@click.option("--org", default=config_github["organization"], show_default=True)
@click.option(
    "--team", default=config_add_students["default_team_slug"], show_default=True
)
def add_students(student_handles, dry, token, org, team):
    """
    student_handles: github user to add (usernames)
    """
    if len(student_handles) == 0:
        print("required handles")
        return 1

    github_students = student_handles
    github_organization = org
    github_team = team
    github_token = token

    ensure_gh_token(github_token)

    # TODO: use logging lib to log messages
    spinner = Halo(stream=sys.stderr)
    if dry:
        spinner.info("Dry run")

    spinner.info("fetch existing team members from GitHub")
    team = Team(github_organization, team_slug=github_team, github_token=github_token)
    num_member = len(team.members.keys())
    words = (
        normal.txt("target team: ")
        .kw(f"{github_team}")
        .txt("( ")
        .kw2(num_member)
        .txt(" members) ")
    )
    spinner.succeed(words.to_str())

    if dry:
        existed_members = set()
    else:
        existed_members = set(team.members.keys())
    outside_users = list(set(github_students) - existed_members)

    # print("Users to invite:")
    # print_table(outside_users, cols=5, wide=15)

    spinner.info("Check valid Github users")
    invalid_id = []
    spinner.start()
    total = len(outside_users)
    for idx, u in enumerate(outside_users, start=1):
        text = "" if not dry else "[skip]: "
        text += f"{idx}/{total} Check valid GitHub username : {u}"
        if dry:
            spinner.succeed(text)
        else:
            if check_is_github_user(u, github_token):
                spinner.succeed(text)
            else:
                spinner.fail(text)
                invalid_id.append(u)

    if len(invalid_id) != 0:
        print("Find non-existed github user names:")
        # control strings take space
        print_table([warn.txt("i").to_str() for i in invalid_id], cols=5, wide=25)

    non_member_valid_users = list(set(outside_users) - set(invalid_id))

    # membership info
    membership_infos = {key: "unknown" for key in non_member_valid_users}
    total = len(non_member_valid_users)
    spinner.info("Check Membership information")
    for idx, username in enumerate(non_member_valid_users, start=1):
        skip = "" if not dry else "[skip]: "
        spinner.start(f"{skip}{idx}/{total}: {username}")
        if not dry:
            res = team.get_memberships(username)
            if res.status_code == 200:
                membership_infos[username] = res.json()["state"]
        spinner.succeed()

    pending_users = [
        u for u in membership_infos.keys() if membership_infos[u] == "pending"
    ]
    no_memship_users = [
        u for u in membership_infos.keys() if membership_infos[u] == "unknown"
    ]

    print(f"Users already in pending state (total:{len(pending_users)}):")
    print_table(pending_users)

    print(f"Users to add (total:{len(no_memship_users)})")
    print_table(no_memship_users)
    print("-" * 30)

    failed_users = []
    spinner.info("start to invite users")
    for user_name in no_memship_users:
        if dry:
            spinner.info(f"[Skip] add user: {user_name}")
        else:
            if True == add_user(team, user_name=user_name):
                spinner.succeed(f"add user: {user_name}")
            else:
                failed_users.append(user_name)
                spinner.fail(f"failed to add user: {user_name}")
    failed_users = list(set(failed_users))

    if len(failed_users) != 0:
        print("Users failed to add")
        print_table(failed_users)

    spinner.succeed("Adding students successfully")


def add_user(team, user_name) -> bool:
    res = team.add_user_to_team(user_name)
    return res.status_code == 200


def check_is_github_user(github_id, github_token) -> bool:
    res = requests.get(
        f"https://api.github.com/users/{github_id}", headers=github_headers(github_token),
    )
    if res.status_code == 200:
        return True
    else:
        return False


if __name__ == "__main__":
    add_students()
