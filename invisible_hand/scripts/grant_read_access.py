import click
import trio
from tqdm import tqdm

from ..config.github import config_github, config_grant_read_access
from ..ensures import ensure_gh_token
from ..utils.github_entities import Team
from ..utils.github_scanner import query_matching_repos

# Use a "team slug"
# for example: "2019 Teaching-team" -> "2019_teaching-team"


@click.command()
@click.argument("hw_title")
@click.option(
    "--token", default=config_github["personal_access_token"], help="github access token"
)
@click.option("--org", default=config_github["organization"], show_default=True)
@click.option(
    "--team", default=config_grant_read_access["reader_team_slug"], show_default=True
)
def grant_read_access(hw_title, token, org, team):
    """Grant read access right of TA's group to students' homework repo"""
    print("start script")

    ensure_gh_token(token)

    teaching_team = Team(org, team, token)

    repos = query_matching_repos(
        org, github_repo_prefix=f"{hw_title}-", github_token=token, verbose=True
    )
    repo_names = [r["name"] for r in repos]

    # show repos to operate on
    ncols = 3
    cols = [repo_names[i::ncols] for i in range(ncols)]
    print("repos to operate on:")
    for a, b, c in zip(*cols):
        print(f"  {a:<30}{b:<30}{c:<}")

    builder = pbar_builder()
    builder.set_config(total=len(repo_names))
    with builder.build(desc="fired") as fired, builder.build(desc="returned") as returned:

        async def subscribe_to_repo(team: Team, repo_name: str):
            res = await team.add_team_repository_async(repo_name, permission="pull")
            if res.status_code != 204:
                print(res)
            returned.update(1)

        async def async_github():
            async with trio.open_nursery() as nursery:
                for repo_name in repo_names:
                    nursery.start_soon(subscribe_to_repo, teaching_team, repo_name)
                    fired.update(1)
                    fired.refresh()
                return

        trio.run(async_github)


class pbar_builder:
    def __cover_dict(self, src, dst):
        for k, v in src.items():
            dst[k] = v

    def __init__(self):
        self.config = {}
        self.next_po = 0

    def set_config(self, **kwargs):
        self.__cover_dict(kwargs, self.config)

    def build(self, **kwargs):
        cfg = {}
        self.__cover_dict(self.config, cfg)
        self.__cover_dict(kwargs, cfg)
        cfg["position"] = self.next_po
        self.next_po += 1
        return tqdm(**cfg)


if __name__ == "__main__":
    grant_read_access()
