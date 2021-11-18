from typing import Final, List, Optional

import typer
from pydantic.error_wrappers import ValidationError
from typer import Option, Argument, Context

# from .cmd_config import app as cmd_config_app
from attr import attrib, attrs
from hand.config import settings
from .check import DoCheck


# Shared Options
class Opt:
    DRY: Final[bool] = Option(
        False, "--dry", help="dry run, would not fire actual requests"
    )
    ACCEPT_ALL: Final[bool] = Option(
        False, "--yes", help="confirm to all", show_default=False
    )


app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Manage your classroom under Github organization.",
)


# @app.callback()
# def main(
#     custom_base: Optional[str] = typer.Option(
#         None, "--custom-base", help="Use custom base folder for configs"
#     ),
# ):
#     """Default callback for every cli invocation"""
#     # load configs
#     print(settings.google_spreadsheet.cred_filename)


@app.command(name="add")
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


@app.command(name="patch")
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


# app.add_typer(cmd_config_app, name="config")

# app.command("add")(add_students)
# app.command("grant-read-access")(grant_read_access)
# app.command("event-times")(event_times)
# app.command("patch-project")(patch_project)
# app.command("crawl-classroom")(crawl_classroom)
# app.command("announce-grade")(announce_grade)

# app.add_typer(config_typer, name="config")
