import click

from colorama import init as colorama_init
from colorama import Fore, Back, Style
from halo import Halo

from ..utils.github_scanner import query_matching_repos
from ..utils.github_entities import Team

from ..config.github import config_github, config_subscribe_hw

colorama_init()


# Use a "team slug"
# for example: "2019 Teaching-team" -> "2019_teaching-team"
@click.command()
@click.argument('hw_title')
@click.option('--token', default=config_github['personal_access_token'], help="github access token")
@click.option('--org', default=config_github['organization'], show_default=True)
@click.option('--team', default=config_subscribe_hw['subscriber_team_slug'], show_default=True)
def subscribe_hw(hw_title, token, org, team):
    '''Grant read access right of TA's group to students' homework repo'''

    teaching_team = Team(org, team, token)

    repos = query_matching_repos(org,
                                 github_repo_prefix=f'{hw_title}-',
                                 github_token=token,
                                 verbose=True)

    with Halo() as spinner:
        spinner.info(f"Operate on team : {teaching_team.team_slug}")

        total = len(repos)
        for idx, r in enumerate(repos, start=1):
            repo_name = r['name']
            spinner.text = f"{idx}/{total} Subscribe to {org}/{repo_name}"
            spinner.start()

            res = teaching_team.add_team_repository(
                repo_name, permission="pull")
            if res.status_code == 204:
                spinner.succeed()
            else:
                spinner.fail()
        spinner.succeed(f"{idx}/{total} Subscribe to student hw repos")


if __name__ == "__main__":
    subscribe_hw()
