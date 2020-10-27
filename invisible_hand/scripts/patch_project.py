import os
import shutil
import subprocess as sp
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import click
import requests
from git import Repo
from git.objects.commit import Commit
from halo import Halo

from invisible_hand.ensures import ensure_gh_token, ensure_git_cached
from ..config.github import config_github
from ..core.color_text import normal, warn
from ..utils.github_scanner import (
    get_github_endpoint_paged_list,
    github_headers,
    query_matching_repos,
)

# The Pull request we made would fetch the first issue which has the same title
# as patch_branch to be the content


@click.command()
@click.argument("hw-prefix")
@click.argument("patch-branch")
@click.option("--source-repo", default="", help="default to tmpl-{hw-prefix}-revise")
@click.option(
    "--token", default=config_github["personal_access_token"], help="github access token"
)
@click.option("--org", default=config_github["organization"], show_default=True)
@click.option("--only-repo", nargs=1, help="only repo to patch")
def patch_project(hw_prefix, patch_branch, source_repo, token, org, only_repo):
    """Patch to student homeworks"""
    ensure_git_cached()
    ensure_gh_token(token)
    # init
    spinner = Halo(stream=sys.stderr)

    if source_repo == "":
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
        normal.txt("Fetch issue template")
        .kw(patch_branch)
        .txt(" from ")
        .kw(source_repo)
        .to_str()
    )
    # Fetch patch template on the source repo
    issues = get_github_endpoint_paged_list(
        endpoint=f"repos/{org}/{source_repo}/issues", github_token=token, verbose=False
    )
    issue_tmpl_found = False
    for i in issues:
        if i["title"].strip() == patch_branch.strip():
            issue_tmpl_found = True
            issue_tmpl_body = i["body"]
            break
    if not issue_tmpl_found:
        raise Exception(f"cannot found issue tmpl `{patch_branch}` on `{source_repo}`")
    spinner.succeed()

    root_folder = Path(
        tempfile.mkdtemp(
            prefix="patch-{}-{}-".format(
                patch_branch, datetime.now().strftime("%b%d%H%M%S")
            ),
            dir=".",
        )
    )

    spinner.succeed(normal.txt("Create tmp folder ").kw(root_folder).to_str())
    spinner.info(
        normal.txt("Fetch soure repo").kw(source_repo).txt(" from GitHub ").to_str()
    )
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
            spinner.info(normal.txt("Only patch to repo : ").kw(repo["name"]).to_str())
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
        pre_prompt_str = (
            normal.txt(f"({repo_idx}/{len(repos)})").kw(f" {r['name']} ").to_str()
        )
        spinner.start()

        # Check if repo already contains the patched branch. Skip if so.
        #  api : https://developer.github.com/v3/git/refs/#get-a-reference
        res = requests.get(
            f"https://api.github.com/repos/{org}/{r['name']}/git/refs/heads/{patch_branch}",
            headers=github_headers(token),
        )
        if res.status_code == 200:  # this branch exists in the remote
            spinner.text = (
                pre_prompt_str + normal.kw("  Skip  ").txt("already patched ").to_str()
            )
            spinner.succeed()
            continue

        spinner.text = pre_prompt_str + normal.txt(" cloning repo...").to_str()
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
            spinner.text = (
                pre_prompt_str + normal.kw2("  Passed  ").txt("Repo no change").to_str()
            )
            spinner.succeed()
            continue

        sp.run(
            ["git", "commit", "-m", f":construction_worker: Patch: {patch_branch}"],
            cwd=student_path / hw_repo_name,
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
        )

        spinner.text = pre_prompt_str + normal.kw(" publish patch to remote...").to_str()
        res = sp.run(
            ["git", "push", "-u", "origin", patch_branch],
            cwd=student_path / hw_repo_name,
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
        )
        if res.returncode != 0:
            spinner.text = (
                pre_prompt_str
                + warn.kw("  Failed  ")
                + warn.txt(" Cannot push branch ")
                .kw2(patch_branch)
                .txt(" to origin")
                .to_str()
            )
            spinner.fail()
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
            spinner.text = pre_prompt_str + normal.txt(" Patched ").to_str()
            spinner.succeed()
        else:
            spinner.text = (
                pre_prompt_str
                + warn.kw("  Failed  ")
                + warn.txt("Cannot create PR")
                .kw2(patch_branch)
                .txt("to origin/master")
                .to_str()
            )
            spinner.fail()
            try:
                info = warn.txt("    ").txt(res.json()["errors"][0]["message"]).to_str()
                print(info)
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
