from pathlib import Path
from typing import List

import iso8601
import typer
from typer import Argument, Option

from hand.config import settings
from hand.exchange import GitHubRepoCommit
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
    dry: bool = Opt.DRY,
):
    """
    Retrieve information about late submissions

    """
    # TODO: take the DRY option into concern

    # <repo-hash> : string in <repo>:<hash> format
    # hw0-ianre657:cb75e99

    result = DoCheck(settings=settings).withOptions(gh_config_valid=True).run()
    if result.success == False:
        typer.echo(result.info)
        raise typer.Abort()

    print("Check deadline format")
    try:
        _ = iso8601.parse_date(deadline)
    except iso8601.ParseError:
        info = f"Invalid time format:{deadline}\n"
        info += f"possible formats: {[t for t in _get_possible_time_formats()]}"
        typer.echo(info)
        raise typer.Abort()

    print("Check input file exists")
    fpath = Path(input_file).expanduser()
    if not fpath.exists():
        typer.echo(f"File not exists :{fpath}")
        raise typer.Abort()

    print("Check input file format")
    with open(fpath, "r") as f:
        try:
            commits = _parse_commit_from_text("".join(f.readlines()))
        except ParseError as err:
            # TODO: educate the user about the right format
            typer.echo(err)
            raise typer.Abort()

    from hand.api.github import GithubAPI
    from hand.scripts import Script
    from hand.scripts.times import ScriptTimes, ScriptTimesDisplayImpl

    gh_api = GithubAPI(token=settings.github.token, org=settings.github.org)
    display = ScriptTimesDisplayImpl(deadline=deadline)
    script: Script = ScriptTimes(
        gh_api=gh_api,
        repos=commits,
        deadline=iso8601.parse_date(deadline),
        display=display,
    )
    script.run()


def _get_possible_time_formats() -> List[str]:
    return ["2020-07-01", "2020-07-01 23:59"]


class ParseError(Exception):
    ...


def _parse_commit_from_text(s: str) -> List[GitHubRepoCommit]:
    result = []
    # substitude all white space character with a space
    raw_inputs = s.split()
    for r in raw_inputs:
        if ":" not in r:
            raise ParseError(f"Expect ':' in string, get:{r}")
        elif r.count(":") > 1:
            raise ParseError("Expect string with only one ':', get:{r}")
        repo, hash = r.split(":")
        result.append(GitHubRepoCommit(name=repo, commit_hash=hash))
    return result
