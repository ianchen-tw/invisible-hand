from typing import Optional

from typer import Argument, Option

from ..check import DoCheck
from ..opt import Opt


def publish_grade(
    homework_prefix: str = Argument(..., help="prefix of the target homework"),
    feedback_source_repo: Optional[str] = Option(
        None, show_default=True, help="Repo contains students' feedbacks"
    ),
    only_id: Optional[str] = Option(default=None, help="only id to announce"),
    dry: bool = Opt.DRY,
    yes: bool = Opt.ACCEPT_ALL,
):
    """Publish student grades to each hw repo"""
    DoCheck(
        gh_config_valid=True, google_client_secret_file_exist=True, git_cached=True
    ).run()

    print("check for only_id")

    # additional check
    print("check feedback source repo exists")
    print("check folder structure of the source repo")
