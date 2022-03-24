from pathlib import Path
from typing import List

from attr import define, field

from hand.api.git import GitApi
from ._protocol import Script


@define
class PatchResource:
    base_dir: Path

    src_dir: Path  # source dir for creating patch
    student_dir: Path

    github_org: str  # we operate repositories under certain organization

    tmpl_repo_name: str

    def _repo_url(self, name):
        return f"https://github.com/{self.github_org}/{name}"

    def _sync_repo(self, repo_path: Path, remote_url: str):
        """ Synchronize a local repository to remote one"""
        api = GitApi()
        if repo_path.exists():
            api.sync_remote(repo_path, remote_url)
        else:
            api.clone_remote(repo_path, remote_url)

    def fetch_student_remotes(self, repo_names: List[str]):
        """Fetch list of student repositories into local folder"""
        for repo in repo_names:
            target_folder = self.student_dir / repo
            self._sync_repo(target_folder, self._repo_url(repo))

    def fetch_pr_template_repo(self):
        """Fetch the main repository to generate pull request"""
        target_folder = self.src_dir / self.tmpl_repo_name
        self._sync_repo(target_folder, self._repo_url(self.tmpl_repo_name))


@define
class PatchResourceBuilder:
    base_dir: Path = field(converter=Path)
    github_org: str
    hw_prefix: str

    tmpl_repo_name: str
    patch_branch: str

    def build(self) -> PatchResource:
        src = self.base_dir / "source_repos"
        student = self.base_dir / "student_repos"

        for d in [self.base_dir, src, student]:
            d.mkdir(exist_ok=True)

        return PatchResource(
            base_dir=self.base_dir,
            src_dir=src,
            github_org=self.github_org,
            student_dir=student,
            tmpl_repo_name=self.tmpl_repo_name,
        )


@define
class ScriptPatchSingleProject(Script):
    """ Publish a patch to a repo by open a Pull Request
    Prerequisite:
        1. the `target_repo` have a local copy
        2. the remote does not have `patch_branch`
    Effect:
        1. Create a new branch on target_repo
        2. Publish patch branch and open a Pull Request
    Options:
        + dry_run:  do not fire request to remote
    """

    # repo: RequestPatchRepo

    pr_body: str

    dry_run: bool

    def run(self):
        pass

    def _repo_exists(self):
        pass
