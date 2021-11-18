from typing import Optional

import typer
from typer import Argument

from ..check import DoCheck
from ..opt import Opt


def patch_project(
    hw: str = Argument(
        default=..., metavar="hw_prefix", help="prefix of the homework title"
    ),
    patch_branch: str = Argument(
        default=..., help="source bracnch to patch to the main branch"
    ),
    # source_repo: Optional[str] = typer.Option(
    #     default=None, help="default to tmpl-{hw-prefix}-revise"
    # ),
    only_repo: Optional[str] = typer.Option(default=None, help="only repo to patch"),
    dry: bool = Opt.DRY,
    yes: bool = Opt.ACCEPT_ALL,
):
    """Patch to student homeworks"""
    DoCheck(gh_config_valid=True, git_cached=True).run()

    if not (yes or typer.confirm(f"Patch homework:{hw} from branch:{patch_branch}?")):
        raise typer.Abort()

    # checks
    print("check source repo exists")
    print("check patch repo exists")
    print("check issue template repo exists")
    print("check target issuse template exists")
