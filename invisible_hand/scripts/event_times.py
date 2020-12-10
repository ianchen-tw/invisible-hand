# github_event_times.py
# Dan Wallach <dwallach@rice.edu>
# Available subject to the Apache 2.0 License
# https://www.apache.org/licenses/LICENSE-2.0

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from pprint import pprint
from typing import List, NamedTuple, Optional, Tuple

import iso8601
import typer
from halo import Halo
from rich.console import Console
from rich.table import Table
from tabulate import tabulate

from invisible_hand.config import app_context
from ..ensures import ensure_config_exists, ensure_gh_token
from ..utils.github_entities import Team
from ..utils.github_scanner import (
    LOCAL_TIMEZONE,
    get_github_endpoint_paged_list,
    localtime_from_iso_datestr,
)
from .shared_options import opt_dry, opt_gh_org, opt_github_token


def is_deadline_passed(dl: datetime, submit: datetime) -> Tuple[bool, timedelta]:
    dl = dl.astimezone(submit.tzinfo)
    if dl < submit:
        return True, submit - dl
    else:
        return False, dl - submit


class commitInfo(NamedTuple):
    commit_hash: str  # 7 characters hash value
    pushed_time: str
    msg: str
    repo: str


class GitHubRepoInfo(NamedTuple):
    name: str
    commit_hash: str  # 7 characters hash value


# python3 github_event_times.py hw0-ianre657:cb75e99
class RepoPrinter:
    def __init__(
        self, repos: List[GitHubRepoInfo], title: str = "Repos",
    ):
        self.repos = repos
        self.title = title

    def print(self):
        table = Table(title=self.title)
        table.add_column("Name", justify="right", style="cyan")
        table.add_column("Commit Hash", justify="left")
        for r in self.repos:
            table.add_row(r.name, r.commit_hash)
        Console().print(table)


def event_times(
    input_file: str = typer.Argument(
        default=..., metavar="hw_path", help="file contains list of repo-hash"
    ),
    deadline: str = typer.Option(
        None,
        "--deadline",
        help="deadline format: 'yyyy-mm-dd' or any ISO8601 format string (timezone will be set to local timezone)",
    ),
    target_team: Optional[str] = typer.Option(
        default=None, help="specific team to operate on"
    ),
    dry: bool = opt_dry,
    token: Optional[str] = opt_github_token,
    org: Optional[str] = opt_gh_org,
):
    """
    Retrieve information about late submissions

    <repo-hash> : string in <repo>:<hash> format
            hw0-ianre657:cb75e99
    """
    ensure_config_exists()

    def fallback(val, fallback_value):
        return val if val else fallback_value

    # Handle default value manually because we'll change our config after app starts up
    deadline: str = fallback(deadline, app_context.config.event_times.deadline)
    token: str = fallback(token, app_context.config.github.personal_access_token)
    org: str = fallback(org, app_context.config.github.organization)

    global github_organization
    global github_token

    typer.echo(f"parse input file : {input_file}")
    try:
        parsed_repos = get_repo_infos(input_file)
    except FileNotFoundError as e:
        print(str(e))
        return
    RepoPrinter(parsed_repos).print()

    ensure_gh_token(token)
    spinner = Halo(stream=sys.stderr)

    github_organization = org
    github_token = token

    print(f"deadline: {deadline}")

    submit_deadline = iso8601.parse_date(deadline)
    submit_deadline = submit_deadline.replace(tzinfo=LOCAL_TIMEZONE)

    spinner.info(f"Deadline : {submit_deadline}")
    success_group = []
    fail_group = []
    spinner.start("Start to check late submissions")
    # sys.exit(0)
    # get team membershup info

    target_repos: List[GitHubRepoInfo] = list(parsed_repos)

    if target_team is not None:
        # Filter repos
        def get_handle(repo_name: str):
            """
                Deduce user handle from user name
                example: hw2-nctulaoda -> nctulaoda
            """
            return re.sub("hw[\d]+-", "", repo_name)

        target_team_members = set(
            Team(
                org=github_organization,
                team_slug=target_team,
                github_token=github_token,
                dry=dry,
            ).members.keys()
        )
        if not dry:
            target_repos = [
                r for r in target_repos if get_handle(r) in target_team_members
            ]

    for idx, repo in enumerate(target_repos, start=1):
        spinner.text = f"({idx}/{len(parsed_repos)}) Checking {repo.name}"
        if dry:
            continue
        result: Optional[commitInfo] = getCommitPushTime(
            org=github_organization, repo=repo.name, commit_hash=repo.commit_hash
        )
        if result:
            passed, delta = is_deadline_passed(
                submit_deadline, iso8601.parse_date(result.pushed_time)
            )
            if passed:
                fail_group.append(
                    {
                        "repo-name": result.repo,
                        "commit-hash": result.commit_hash,
                        "time-passed": delta,
                        "last-pushtime": result.pushed_time,
                    }
                )
            else:
                success_group.append((result, delta))

    spinner.succeed("Check finished")
    print("=" * 20, "REPORT", "=" * 20)
    print(f"Total submissions : {len(parsed_repos)}")
    print(f"late submissions: {len(fail_group)}")
    print(f"Submission Deadline: {submit_deadline}")
    print(tabulate(fail_group, headers="keys"))


def get_repo_infos(filename: str) -> List[GitHubRepoInfo]:
    st = Path(filename).read_text()
    infos = st.split()
    result = []
    for r in infos:
        repo, commit_hash = r.split(":")
        result.append(GitHubRepoInfo(repo, commit_hash))
    return result


def getCommitPushTime(org: str, repo: str, commit_hash: str) -> Optional[commitInfo]:
    """Find the push-time of given commit-hash
    """
    global github_token
    response = get_github_endpoint_paged_list(
        f"repos/{org}/{repo}/events", github_token, verbose=False
    )
    event_list = [x for x in response if x["type"] == "PushEvent"]
    for event in event_list:
        try:
            github_id = event["actor"]["login"]
            date = localtime_from_iso_datestr(event["created_at"])
            target_commits = [
                x for x in event["payload"]["commits"] if x["sha"][0:7] == commit_hash
            ]

            if len(target_commits) == 0:
                continue
            elif len(target_commits) >= 2:
                print("SHA Conflict for user: {}".format(github_id))
            else:
                target_commit = target_commits[0]

                commit_message = tex_escape(
                    target_commit["message"].splitlines()[0]
                )  # only the first line if multiline
                commit_hash = target_commit["sha"][0:7]

                return commitInfo(commit_hash, date, commit_message, repo)
        except KeyError:
            print("Error: malformed event!")
            pprint(event)
    return None


# https://stackoverflow.com/questions/16259923/how-can-i-escape-latex-special-characters-inside-django-templates


def tex_escape(text: str) -> str:
    """
    :param text: a plain text message
    :return: the message escaped to appear correctly in LaTeX
    """
    conv = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\^{}",
        "\\": r"\textbackslash{}",
        "<": r"\textless{}",
        ">": r"\textgreater{}",
    }
    regex = re.compile(
        "|".join(
            re.escape(str(key))
            for key in sorted(conv.keys(), key=lambda item: -len(item))
        )
    )
    return regex.sub(lambda match: conv[match.group()], text)
