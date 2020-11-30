import os
import shutil
import subprocess as sp
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from requests.api import patch

import typer
import requests
from git import Repo
from git.objects.commit import Commit
from halo import Halo

from invisible_hand.ensures import ensure_gh_token, ensure_git_cached
from ..shared_options import opt_gh_org, opt_github_token
from ..core.console_color import kw, safe, danger
from invisible_hand import console_txt, console
from ..utils.github_scanner import (
    get_github_endpoint_paged_list,
    github_headers,
    query_matching_repos,
)

# The Pull request we made would fetch the first issue which has the same title
# as patch_branch to be the content


def patch_project(
    hw_prefix: str = typer.Argument(default=..., help="prefix of the homework title"),
    patch_branch: str = typer.Argument(
        default=..., help="source bracnch to patch to the main branch"
    ),
    source_repo: Optional[str] = typer.Option(
        default=None, help="default to tmpl-{hw-prefix}-revise"
    ),
    only_repo: Optional[str] = typer.Option(default=None, help="only repo to patch"),
    dry: bool = typer.Option(
        False, "--dry", help="dry run, do not publish result to the remote"
    ),
    token: str = opt_github_token,
    org: str = opt_gh_org,
):
    """Patch to student homeworks"""

    ensure_git_cached()
    ensure_gh_token(token)
    # init
    spinner = Halo(stream=sys.stderr)

    if not source_repo:
        source_repo = f"tmpl-{hw_prefix}-revise"

    # Check if repo already contains the patched branch. Skip if so.
    #  api : https://developer.github.com/v3/git/refs/#get-a-reference
    res = requests.get(
        f"https://api.github.com/repos/{org}/{source_repo}/git/refs/heads/{patch_branch}",
        headers=github_headers(token),
    )
    if res.status_code != 200:  # this branch not exists on the remote
        spinner.fail(
            f"branch : `{patch_branch}` doesn't exist on repo:{org}/{source_repo} "
        )
        return

    cur = Path(".")
    for d in cur.glob("patch-*"):
        shutil.rmtree(d)
    spinner.info("delete dated folder")

    spinner.start(
        console_txt(f"Fetch issue template {kw(patch_branch)} from {kw(source_repo)}")
    )
    # Fetch patch template on the source repo
    issues = get_github_endpoint_paged_list(
        endpoint=f"repos/{org}/{source_repo}/issues", github_token=token, verbose=False
    )

    def find_target_issue() -> Optional[Dict]:
        for issue in issues:
            if issue["title"].strip() == patch_branch.strip():
                return issue
        return None

    target_issue = find_target_issue()
    if not target_issue:
        raise Exception(f"cannot found issue tmpl `{patch_branch}` on `{source_repo}`")
    issue_tmpl_body = target_issue["body"]
    spinner.succeed()

    root_folder = Path(
        tempfile.mkdtemp(
            prefix="patch-{}-{}-".format(
                patch_branch, datetime.now().strftime("%b%d%H%M%S")
            ),
            dir=".",
        )
    )

    spinner.succeed(console_txt(f"Create tmp folder: {kw(root_folder)}"))
    spinner.info(console_txt(f"Fetch source repo {kw(source_repo)} from Github"))
    src_repo_path = root_folder / "source_repo"
    sp.run(
        [
            "git",
            "clone",
            f"https://github.com/{org}/{source_repo}.git",
            src_repo_path.name,
        ],
        cwd=root_folder,
    )

    src_repo = Repo(src_repo_path)
    sp.run(
        ["git", "checkout", "--track", f"origin/{patch_branch}"],
        cwd=src_repo_path,
        stdout=sp.DEVNULL,
        stderr=sp.DEVNULL,
    )
    spinner.succeed()

    # Pasting changed files into students repo
    src_repo_git = src_repo.git
    src_repo_git.checkout(patch_branch)
    changed_files, renamed_files = get_changed_files(
        master_commit=src_repo.heads["master"].commit,
        patch_commit=src_repo.heads[patch_branch].commit,
    )

    spinner.start("Fetch information for homework repo")
    spinner.succeed()
    if only_repo is not None:
        repos = [
            re
            for re in query_matching_repos(
                org, github_repo_prefix=only_repo, github_token=token, verbose=False
            )
            if re["name"] == only_repo
        ]
        repo = next(iter(repos), None)
        if repo:
            spinner.info(console_txt(f"Only patch to repo : " + kw(repo["name"])))
        repos = [repo]
    else:
        repos = query_matching_repos(
            org, github_repo_prefix=hw_prefix, github_token=token, verbose=False
        )
    spinner.succeed()

    # Patch to student repos
    student_path = root_folder / "student_repos"
    student_path.mkdir()
    for repo_idx, r in enumerate(repos, start=1):
        pre_prompt_str = console_txt(f"({repo_idx}/{len(repos)}) " + kw(r["name"]))
        spinner.start()

        # Check if repo already contains the patched branch. Skip if so.
        #  api : https://developer.github.com/v3/git/refs/#get-a-reference
        res = requests.get(
            f"https://api.github.com/repos/{org}/{r['name']}/git/refs/heads/{patch_branch}",
            headers=github_headers(token),
        )
        if res.status_code == 200:  # this branch exists in the remote
            spinner.text = pre_prompt_str + console_txt(
                safe(" Skip ") + " already patched"
            )
            spinner.succeed()
            continue

        spinner.text = pre_prompt_str + "cloning repo"

        sp.run(
            ["git", "clone", "--depth=1", r["html_url"]],
            cwd=student_path,
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
        )

        hw_repo_name = r["html_url"].rsplit("/")[-1]

        # open a new branch & checkout to that branch
        sp.run(
            ["git", "checkout", "-b", patch_branch],
            cwd=student_path / hw_repo_name,
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
        )

        # copy file to student repo
        for f in changed_files.keys():
            (student_path / hw_repo_name / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src=src_repo_path / f, dst=student_path / hw_repo_name / f)
        for f in renamed_files.keys():
            os.remove(student_path / hw_repo_name / f)

        # changed_files = get_changed_files(
        #     master_commit = src_repo.heads['master'].commit,
        #     patch_commit = src_repo.heads[patch_branch].commit
        # )
        # push (publish) that branch to student repo
        sp.run(
            ["git", "add", "."],
            cwd=student_path / hw_repo_name,
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
        )

        # Pass if no changed
        student_repo = Repo(student_path / hw_repo_name)
        if len(student_repo.index.diff("HEAD")) == 0:
            spinner.text = pre_prompt_str + console_txt(
                safe(" Passed ") + " no changes in repo"
            )
            spinner.succeed()
            continue

        sp.run(
            ["git", "commit", "-m", f":construction_worker: Patch: {patch_branch}"],
            cwd=student_path / hw_repo_name,
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
        )

        spinner.text = pre_prompt_str + console_txt(kw(" publish patch to remote..."))
        if dry:
            spinner.succeed(pre_prompt_str + console_txt(safe(" Patched ")))
            continue
        res = sp.run(
            ["git", "push", "-u", "origin", patch_branch],
            cwd=student_path / hw_repo_name,
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
        )
        if res.returncode != 0:
            spinner.fail(
                pre_prompt_str
                + console_txt(
                    danger("  Failed  ")
                    + f"Cannot push branch {kw(patch_branch)} to_origin"
                )
            )
            continue

        # open an pull-request on students repo
        # student_repo/patch-branch  -> student_repo/master
        body = {
            "title": f"[PATCH] {patch_branch}",
            "body": issue_tmpl_body,
            "head": patch_branch,
            "base": "master",
        }
        res = requests.post(
            f"https://api.github.com/repos/{org}/{r['name']}/pulls",
            headers=github_headers(token),
            json=body,
        )
        if res.status_code == 201:
            spinner.text = pre_prompt_str + console_txt(safe(" Patched "))
            spinner.succeed()
        else:
            spinner.fail(
                pre_prompt_str
                + console_txt(
                    danger("  Failed  ")
                    + f"Cannot create PR {kw(patch_branch)} to origin/master"
                )
            )
            try:
                console.print(res.json()["errors"][0]["message"])
            except:
                pass
            continue

    # TODO : print summary after patch
    #       how many success, skiped, failed


def get_changed_files(master_commit: Commit, patch_commit: Commit):
    # TODO
    #  git change type support:
    #  A: addition of a file
    #  C: copy of a file into a new one
    #  D: deletion of a file
    # done  M: modification of the contents or mode of a file
    #  R: renaming of a file
    #  T: change in the type of the file
    #  U: file is unmerged (you must complete the merge before it can be committed)
    #  X: "unknown" change type (most probably a bug, please report it)
    changed_files = {}
    renamed_files = {}
    for x in master_commit.diff(patch_commit):
        # Change type of x is not 'new'
        if x.a_blob != None and x.a_blob.path not in changed_files.keys():
            if x.change_type == "R":
                # file have been renamed, the dest file is include in the changed files
                # so we need to delete this file from dest repo

                # print(f'a remove(rename) :{x.a_blob.path}, type: {x.change_type}')
                renamed_files[x.a_blob.path] = {"type": x.change_type}
            else:
                # print(f'a change :{x.a_blob.path}, type: {x.change_type}')
                changed_files[x.a_blob.path] = {"type": x.change_type}

        # Change type of x is not 'delete'
        if x.b_blob is not None and x.b_blob.path not in changed_files.keys():
            # print(f'b change :{x.b_blob.path}, type: {x.change_type}')
            changed_files[x.b_blob.path] = {"type": x.change_type}

    return changed_files, renamed_files


if __name__ == "__main__":
    patch_project()
