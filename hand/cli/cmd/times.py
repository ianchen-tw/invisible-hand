from pathlib import Path
from typing import Optional

import typer
from typer import Argument, Option

from hand.config import settings
from ..check import DoCheck
from ..opt import Opt


def event_times(
    input_file: str = Argument(
        default=..., metavar="hw_path", help="file contains list of repo-hash"
    ),
    deadline: str = Option(
        None,
        "--deadline",
        help="deadline format: 'yyyy-mm-dd' or any ISO8601 format string (timezone will be set to local timezone)",
    ),
    target_team: Optional[str] = Option(
        default=None, help="specific team to operate on"
    ),
    dry: bool = Opt.DRY,
):
    """
    Retrieve information about late submissions

    <repo-hash> : string in <repo>:<hash> format
            hw0-ianre657:cb75e99
    """

    result = DoCheck(settings=settings).withOptions(gh_config_valid=True).run()
    if result.success == False:
        typer.echo(result.info)
        raise typer.Abort()

    print("Check input file exists")
    f = Path(input_file).expanduser()
    if not f.exists():
        typer.echo(f"File not exists :{f}")
        raise typer.Abort()

    # additional checks
    print("check input file format")
