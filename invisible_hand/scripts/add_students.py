import click
from typing import List, Dict

import requests

from halo import Halo

from ..core.color_text import normal, warn
from ..config.github import config_github, config_add_students
from ..utils.github_scanner import github_headers
from ..utils.github_entities import Team
from ..ensures import ensure_gh_token


def print_table(data, cols=5, wide=15, indent=2):
    '''Prints formatted data on columns of given width.'''
    n, r = divmod(len(data), cols)
    pat = '{{:{}}}'.format(wide)
    line = '\n{}'.format(' '*indent).join(pat * cols for _ in range(n))

    # indent the first line
    line = ' '*indent + line

    last_line = ' '*indent + pat * r
    print(line.format(*data))
    print(last_line.format(*data[n*cols:]))


# Use a "team slug"
# for example: "2019 Students-hello" -> "2019_students-hello"

@click.command()
@click.argument('student_handles', nargs=-1)
@click.option('--token', default=config_github['personal_access_token'], help="github access token")
@click.option('--org', default=config_github['organization'], show_default=True)
@click.option('--team', default=config_add_students['default_team_slug'], show_default=True)
def add_students(student_handles, token, org, team):
    '''
    student_handles: github user to add (usernames)
    '''
    if len(student_handles) == 0:
        print(f'required handles')
        return 1

    github_students = student_handles
    github_organization = org
    github_team = team
    github_token = token

    ensure_gh_token(github_token)

    #print('org: {}'.format(github_organization))
    #print('token: {}'.format(github_token))
    # print("students:{}".format(github_students))

    with Halo() as spinner:
        spinner.text = "fetch existing team members from GitHub"
        team = Team(github_organization, team_slug=github_team,
                    github_token=github_token)
        spinner.succeed()

        num_member = len(team.members.keys())
        words = normal.txt('target team: ').kw(
            f'{github_team}').txt('( ').kw2(num_member).txt(' members) ')
        spinner.info(words.to_str())

    existed_members = set(team.members.keys())
    outside_users = list(set(github_students)-existed_members)

    #print("Users to invite:")
    #print_table(outside_users, cols=5, wide=15)

    invalid_id = []
    with Halo() as spinner:
        spinner.text = ""
        # spinner.start()
        total = len(outside_users)
        for idx, u in enumerate(outside_users, start=1):
            spinner.text = "{}/{} Check valid GitHub username : {}".format(
                idx, total, u)
            if check_is_github_user(u, github_token) == False:
                invalid_id.append(u)
        spinner.text = "{}/{} Check valid GitHub username".format(total, total)
        spinner.succeed()

    if len(invalid_id) != 0:
        print("Find non-existed github user names:")
        # control strings take space
        print_table([warn.txt(f'i').to_str() for i in invalid_id],
                    cols=5, wide=25)

    non_member_valid_users = list(set(outside_users) - set(invalid_id))

    # membership info
    membership_infos = {key: "unknown" for key in non_member_valid_users}
    with Halo() as spinner:
        spinner.text = "Check Membership information"
        spinner.start()
        total = len(non_member_valid_users)
        for idx, username in enumerate(non_member_valid_users, start=1):
            spinner.text = "{}/{} Check Membership information : {}".format(
                idx, total, username)
            res = team.get_memberships(username)
            if res.status_code == 200:
                membership_infos[username] = res.json()['state']
        spinner.text = "{}/{} Check Membership information".format(
            total, total)
        spinner.succeed()

    pending_users = [u for u in membership_infos.keys(
    ) if membership_infos[u] == "pending"]
    no_memship_users = [
        u for u in membership_infos.keys() if membership_infos[u] == "unknown"]

    print("Users already in pending state (total:{}):".format(len(pending_users)))
    print_table(pending_users)

    print("Users to add (total: {})".format(len(no_memship_users)))
    print_table(no_memship_users)

    failed_users = []
    with Halo() as spinner:
        for user_name in no_memship_users:
            spinner.text = normal.txt('adding user: ').kw(user_name).to_str()
            spinner.start()
            res = team.add_user_to_team(user_name)
            if res.status_code == 200:
                spinner.succeed()
            else:
                failed_users.append(user_name)
                spinner.text += warn.txt(', return code:').kw(
                    f' {res.status_code} ').to_str()
                spinner.fail()
    failed_users = list(set(failed_users))

    if len(failed_users) != 0:
        print("Users failed to add")
        print_table(failed_users)

    with Halo() as spinner:
        spinner.text = "Adding students successfully"
        spinner.info()


def check_is_github_user(github_id, github_token) -> bool:
    res = requests.get("https://api.github.com/users/{}".format(github_id),
                       headers=github_headers(github_token))
    if res.status_code == 200:
        return True
    else:
        return False


if __name__ == "__main__":
    add_students()
