import click
from colorama import init as colorama_init
from colorama import Fore, Back, Style
from halo import Halo

from ..utils.github_scanner import query_matching_repos
from ..config.github import config_github
from ..utils.github_entities import Team


# Use a "team slug"
# for example: "2019 Teaching-team" -> "2019_teaching-team"
DEFAULT_GITHUB_TEAM = "2019-teaching-team"
DEFAULT_REPO_PREFIX = "hw0-"


@click.command()
@click.argument('hw-prefix')
@click.option('--org', default=config_github['organization'], show_default=True)
@click.option('--token', default=config_github['personal_access_token'], help="github access token")
@click.option('--team', default=DEFAULT_GITHUB_TEAM, help="GitHub team to add students into", show_default=True)
def grant_team_access(org, team,token,hw_prefix):
    '''Add students into a github team

        hw-prefix: prefix for repos to subscribe
    '''

    colorama_init()

    github_organization = org
    github_team = team
    github_token = token
    github_repo_prefix = hw_prefix

    teaching_team = Team(github_organization, github_team, github_token)

    repos = query_matching_repos(github_organization,
                                 github_repo_prefix=github_repo_prefix,
                                 github_token=github_token,
                                 verbose=True)

    with Halo() as spinner:
        spinner.text = "Operate on team : {}".format(teaching_team.team_slug)
        spinner.info()

        spinner.text = ""
        spinner.start()

        total = len(repos)
        for idx, r in enumerate(repos, start=1):
            repo_name = r['name']
            spinner.text = "{}/{} Subscribe to {}/{}".format(
                idx, total, teaching_team.org, repo_name)

            res = teaching_team.add_team_repository(
                repo_name, permission="pull")
            if res.status_code == 204:
                spinner.succeed()
            else:
                spinner.fail()
        spinner.text = "{}/{} Subscribe to student hw repos".format(idx, total)
        spinner.succeed()


if __name__ == "__main__":
    grant_team_access()
