from typing import List

import typer
from typer import Argument

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

    result = DoCheck(settings=settings).withOptions(gh_config_valid=True).run()
    if result.success == False:
        typer.echo(result.info)
        raise typer.Abort()

    org, team = settings.github.org, settings.add.student_team

    if not (yes or typer.confirm(f"Add students to {org}/{team}?")):
        raise typer.Abort()

    # add some checks before running the script
    print(f"check student team exists {team}")

    from hand.scripts import Script
    from hand.scripts.add import ScriptAddStudents

    script: Script = ScriptAddStudents(
        gh_invite_team=team, user_handles=handles, dry_run=dry
    )
    script.run()
