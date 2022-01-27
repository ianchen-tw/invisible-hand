from datetime import datetime, timedelta
from typing import List, Optional

from attr import attrs

from hand.api.github import GithubAPI
from hand.exchange import GitHubCommitInfo, GitHubRepoCommit
from ._protocol import Script


@attrs(auto_attribs=True)
class ScriptTimes(Script):
    gh_api: GithubAPI
    repos: List[GitHubRepoCommit]
    deadline: datetime

    def run(self):
        self._do_run()

    def _do_run(self):
        result: List[DeadLinePassed] = []

        for repo in self.repos:
            commit_info = _get_commit_push_time(self.gh_api, repo)
            if commit_info is None:
                # TODO: warning
                continue

            time_passed: Optional[timedelta] = _check_deadline(
                self.deadline, commit_info.pushed_time
            )
            if time_passed:
                p = DeadLinePassed.from_commit_info(commit_info, time_passed)
                result.append(p)


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


def _get_commit_push_time(
    gh_api: GithubAPI, repo_commit: GitHubRepoCommit
) -> Optional[GitHubCommitInfo]:
    """ Get the push time of a certain git commit
    """


def _check_deadline(deadline: datetime, provided: datetime) -> Optional[timedelta]:
    deadline = deadline.astimezone(provided.tzinfo)
    return (provided - deadline) if deadline < provided else None
