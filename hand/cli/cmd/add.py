from typing import List

import typer
from typer import Argument

# from .cmd_config import app as cmd_config_app
from hand.config import settings
from ..check import DoCheck
from ..opt import Opt


def add_students(
    handles: List[str] = Argument(
        metavar="student_handles",
        default=...,
        help="list of student handles separated by white space",
    ),
    yes: bool = Opt.ACCEPT_ALL,
    dry: bool = Opt.DRY,
):
    """Add student to Github Organization"""
    DoCheck(gh_config_valid=True).run()

    org, team = settings.github.org, settings.add.student_team

    if not (yes or typer.confirm(f"Add students to {org}/{team}?")):
        raise typer.Abort()

    # add some checks before running the script
    print(f"check student team exists {team}")

    from hand.scripts.add import ScriptAddStudents

    ScriptAddStudents(gh_invite_team=team, user_handles=handles, dry_run=dry).run()
