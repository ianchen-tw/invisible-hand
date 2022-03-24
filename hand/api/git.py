import os
from pathlib import Path

import git
from attr import define
from loguru import logger as log


@define
class GitApi:
    def clone_remote(self, dst: Path, remote_url: str):
        """Clone a remote repository into a local folder"""
        git.Repo.clone_from(remote_url, dst)
        log.info(f"clone repo: {remote_url} -> {dst}")

    def sync_remote(self, dst: Path, remote_url: str):
        """Synchronize a folder in dst with a git repo specified in remote url"""
        r: git.Repo = git.Repo(dst)
        remote = git.Remote(repo=r, name="origin").set_url(remote_url)
        # Remove untracked files
        for f in r.untracked_files:
            target = Path(dst / f)
            os.remove(target)
            log.info(f"remove untracked file: {target}")
        # Reset current tree and update to remote head
        r.heads[0].checkout(force=True)
        remote.pull()
