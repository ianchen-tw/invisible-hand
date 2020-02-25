import argparse
from colorama import init as colorama_init
from colorama import Fore, Back, Style
from halo import Halo


from github_scanner import query_matching_repos
from github_config import default_github_token, default_github_organization
from github_entities import Team

colorama_init()


# Use a "team slug"
# for example: "2019 Teaching-team" -> "2019_teaching-team"
DEFAULT_GITHUB_TEAM = "2019-teaching-team"
DEFAULT_REPO_PREFIX = "hw0-"


parser = argparse.ArgumentParser(
    description='Add students into a github team.')
parser.add_argument('--token',
                    nargs=1,
                    default=[default_github_token],
                    help="GitHub API token")
parser.add_argument('--org',
                    nargs=1,
                    default=[default_github_organization],
                    help='GitHub organization to operate, default: ' + default_github_organization)
parser.add_argument('--team',
                    nargs=1,
                    default=[DEFAULT_GITHUB_TEAM],
                    help='GitHub team to add students into: ' + DEFAULT_GITHUB_TEAM)

parser.add_argument('--repo_prefix',
                    nargs=1,
                    default=[DEFAULT_REPO_PREFIX],
                    help='prefix for repos to subscribe')

args = parser.parse_args()
github_organization = args.org[0]
github_team = args.team[0]
github_token = args.token[0]
github_repo_prefix = args.repo_prefix[0]


def main():

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
    main()
