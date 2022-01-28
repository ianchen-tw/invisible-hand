from datetime import datetime, timedelta
from typing import List, Optional, Protocol

import humanize
import iso8601
from attr import attrib, attrs
from rich.console import Console
from rich.table import Table

from hand.api.github import GithubAPI
from hand.exchange import GitHubCommitInfo, GitHubRepoCommit
from ._protocol import Script


@attrs(auto_attribs=True)
class DeadLinePassed:
    repo_name: str
    commit_hash: str
    last_pushtime: str
    time_passed: timedelta

    @classmethod
    def from_commit_info(
        cls, c: GitHubCommitInfo, time_passed: timedelta
    ) -> "DeadLinePassed":
        return DeadLinePassed(
            repo_name=c.repo,
            commit_hash=c.commit_hash,
            last_pushtime=c.pushed_time,
            time_passed=time_passed,
        )


class ScriptTimesDisplay(Protocol):
    def add_result_dlpassed(self, p: DeadLinePassed):
        """Displaying output to the user"""
        ...

    def print_report(self):
        """Display the execution report"""
        ...


@attrs(auto_attribs=True)
class ScriptTimesDisplayImpl(ScriptTimesDisplay):

    deadline: str
    nm_queried: int = attrib(default=0)
    dl_passed: List[DeadLinePassed] = attrib(factory=list)

    def add_result_dlpassed(self, p: DeadLinePassed):
        self.dl_passed.append(p)

    def print_report(self):
        t = Table(title=f"Late Submissions: deadline - [red]{self.deadline}",)
        t.add_column("Repo", justify="right", no_wrap=True)
        t.add_column("Submit time")
        t.add_column("Delta")
        t.add_column("Commit Hash")

        for r in self.dl_passed:
            t.add_row(
                r.repo_name,
                r.last_pushtime,
                f"{humanize.naturaldelta(r.time_passed)} after",
                r.commit_hash,
            )
        console = Console()
        console.print()
        console.print(t)


@attrs(auto_attribs=True)
class ScriptTimes(Script):
    gh_api: GithubAPI
    repos: List[GitHubRepoCommit]
    deadline: datetime
    display: ScriptTimesDisplay = attrib(factory=ScriptTimesDisplay)

    def run(self):
        self._do_run()

    def _do_run(self):
        for repo in self.repos:
            commit_info = _get_commit_push_time(self.gh_api, repo)
            if commit_info is None:
                # TODO: warning
                continue

            time_passed: Optional[timedelta] = _check_deadline(
                self.deadline, iso8601.parse_date(commit_info.pushed_time)
            )
            if time_passed:
                p = DeadLinePassed.from_commit_info(commit_info, time_passed)
                self.display.add_result_dlpassed(p)
        self.display.print_report()


def _get_commit_push_time(
    gh_api: GithubAPI, repo_commit: GitHubRepoCommit
) -> Optional[GitHubCommitInfo]:
    """ Get the push time of a certain git commit
    """
    ptime: str = gh_api.get_commit_pushed_time(repo_commit)
    if ptime is None:
        return None
    return GitHubCommitInfo(
        commit_hash=repo_commit.commit_hash, pushed_time=ptime, repo=repo_commit.name,
    )


def _check_deadline(deadline: datetime, provided: datetime) -> Optional[timedelta]:
    deadline = deadline.astimezone(provided.tzinfo)
    return (deadline - provided) if deadline < provided else None
