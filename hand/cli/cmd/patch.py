import tempfile
from pathlib import Path
from typing import List, Optional

import typer
from attr import define
from typer import Argument

from hand.config import settings
from ..check import DoCheck
from ..opt import Opt


@define
class PatchResource:
    base_folder: Path

    @classmethod
    def Create(cls, cwd: Path):
        base = tempfile.mkdtemp(prefix="prefix", dir=cwd,)
        return PatchResource(base_folder=base)


def patch_project(
    hw: str = Argument(
        default=..., metavar="hw_prefix", help="prefix of the homework title"
    ),
    patch_branch: str = Argument(
        default=..., help="source bracnch to patch to the main branch"
    ),
    src_repo: Optional[str] = typer.Option(
        default=None, help="default to tmpl-{hw-prefix}-revise"
    ),
    only_repo: Optional[str] = typer.Option(default=None, help="only repo to patch"),
    dry: bool = Opt.DRY,
    yes: bool = Opt.ACCEPT_ALL,
):
    """Patch to student homeworks"""
    DoCheck(gh_config_valid=True, git_cached=True).run()
    if not (yes or typer.confirm(f"Patch homework:{hw} from branch:{patch_branch}?")):
        raise typer.Abort()

    # checks
    from hand.api.github import GithubAPI

    gh = GithubAPI(token=settings.github.token, org=settings.github.org)

    # Check source repo exists
    if not gh.repo_exists(src_repo):
        print(
            f"Repo not exists: {src_repo}, which is neccessary to fetch patch project"
        )
        raise typer.Abort()

    # Check patch branch exists
    if not gh.remote_branch_exists(repo=src_repo, branch=patch_branch):
        print(f"Branch({patch_branch}) not exists on repo:{src_repo}")
        raise typer.Abort()

    # Issue template must exists
    print("check target issuse template exists")
    if not gh.find_issue_with_title(repo=src_repo, title=patch_branch):
        print(
            f"cannot found issue template with name '{patch_branch}', in repo: {src_repo}"
        )
        raise typer.Abort()

    # Get final output repo
    target_repos: List[str]
    if only_repo is not None:
        [only_repo]
    else:
        # target_repos = gh.query_repo_with_prefix(prefix=hw)
        pass

    # Prepare data
    from hand.scripts.patch import PatchResourceBuilder

    res = PatchResourceBuilder(
        base_dir="patch_resource",
        github_org="compiler-f19",
        hw_prefix="hw3",
        tmpl_repo_name="tmpl-hw3-revise",
        patch_branch="0-fix-var-name",
    ).build()

    res.fetch_student_remotes(["hw3-ianre657"])
    res.fetch_pr_template_repo()

    # TODO: use a stream line approach

    #  We will gather information first
    # We will ask github which projects need to be patched by exploring their issues
