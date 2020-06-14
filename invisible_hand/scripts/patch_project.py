import os
import sys
import shutil
import tempfile
import subprocess as sp
import requests
from datetime import datetime
from pathlib import Path

import click

from git import Repo, IndexFile
from git.objects.commit import Commit

from halo import Halo
from colorama import init as colorama_init
from colorama import Fore, Back, Style


from ..utils.github_scanner import query_matching_repos, github_headers, get_github_endpoint_paged_list, query_matching_repos
from ..config.github import config_github



# The Pull request we made would fetch the first issue which has the same title
# as patch_branch to be the content


@click.command()
@click.argument('hw-prefix')
@click.argument('patch-branch')
@click.option('--source-repo', default='', help="default to tmpl-{hw-prefix}-revise")
@click.option('--token', default=config_github['personal_access_token'], help="github access token")
@click.option('--org', default=config_github['organization'], show_default=True)
@click.option('--only-repo', nargs=1, help="only repo to patch")
def patch_project(hw_prefix, patch_branch, source_repo, token, org, only_repo):
    '''Patch to student homeworks'''
    # init
    colorama_init(autoreset=True)
    spinner = Halo(stream=sys.stderr)

    if source_repo == '':
        source_repo = f'tmpl-{hw_prefix}-revise'

    # Check if repo already contains the patched branch. Skip if so.
    #  api : https://developer.github.com/v3/git/refs/#get-a-reference
    res = requests.get(
        f"https://api.github.com/repos/{org}/{source_repo}/git/refs/heads/{patch_branch}", headers=github_headers(token))
    if res.status_code != 200:  # this branch not exists on the remote
        spinner.fail(f"branch : `{patch_branch}` doesn't exist on repo:{org}/{source_repo} ")
        return

    cur = Path('.')
    for d in cur.glob("patch-*"):
        shutil.rmtree(d)
    spinner.info("delete dated folder")

    spinner.start(
        f"Fetch issue template {Fore.CYAN}{patch_branch} {Fore.RESET}from {Fore.CYAN}{source_repo}")
    # Fetch patch template on the source repo
    issues = get_github_endpoint_paged_list(
        endpoint=f"repos/{org}/{source_repo}/issues",
        github_token=token,
        verbose=False
    )
    issue_tmpl_found = False
    for i in issues:
        if i['title'].strip() == patch_branch.strip():
            issue_tmpl_found = True
            issue_tmpl_body = i['body']
            break
    if not issue_tmpl_found:
        raise Exception(
            f"cannot found issue tmpl `{patch_branch}` on `{source_repo}`")
    spinner.succeed()

    root_folder = Path(tempfile.mkdtemp(
        prefix="patch-{}-{}-".format(patch_branch, datetime.now().strftime("%b%d%H%M%S")), dir="."))
    spinner.succeed(f"Create tmp folder {Fore.YELLOW}{root_folder}")

    spinner.info(
        f"Fetch source repo {Fore.CYAN}{source_repo}{Style.RESET_ALL} from GitHub")
    src_repo_path = root_folder / "source_repo"
    sp.run(['git', 'clone',
            f'https://github.com/{org}/{source_repo}.git', src_repo_path.name, ], cwd=root_folder)

    src_repo = Repo(src_repo_path)
    sp.run(['git', 'checkout', '--track', f'origin/{patch_branch}'],
           cwd=src_repo_path, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    spinner.succeed()

    # Pasting changed files into students repo
    src_repo_git = src_repo.git
    src_repo_git.checkout(patch_branch)
    changed_files, renamed_files = get_changed_files(
        master_commit=src_repo.heads['master'].commit,
        patch_commit=src_repo.heads[patch_branch].commit
    )

    spinner.start("Fetch information for homework repo")
    spinner.succeed()
    if only_repo is not None:
        repos = [re for re in query_matching_repos(org,
                                                   github_repo_prefix=only_repo,
                                                   github_token=token,
                                                   verbose=False) if re['name'] == only_repo]
        repo = next(iter(repos), None)
        if repo:
            spinner.info(
                f"Only patch to repo : {Fore.YELLOW}{repo['name']}{Style.RESET_ALL}")
        repos = [repo]
    else:
        repos = query_matching_repos(org,
                                     github_repo_prefix=hw_prefix,
                                     github_token=token,
                                     verbose=False)
    spinner.succeed()

    # Patch to student repos
    student_path = root_folder / "student_repos"
    student_path.mkdir()
    for repo_idx, r in enumerate(repos, start=1):
        pre_prompt_str = f"({repo_idx}/{len(repos)}) {Fore.YELLOW}{r['name']}{Fore.RESET}"
        spinner.start()

        # Check if repo already contains the patched branch. Skip if so.
        #  api : https://developer.github.com/v3/git/refs/#get-a-reference
        res = requests.get(
            f"https://api.github.com/repos/{org}/{r['name']}/git/refs/heads/{patch_branch}", headers=github_headers(token))
        if res.status_code == 200:  # this branch exists in the remote
            spinner.text = pre_prompt_str + \
                f" {Back.GREEN}{Fore.BLACK} Skip {Style.RESET_ALL} already patched"
            spinner.succeed()
            continue

        spinner.text = pre_prompt_str + \
            f" {Fore.BLUE}cloning repo..{Fore.RESET}"
        sp.run(['git', 'clone', '--depth=1', r['html_url']],
               cwd=student_path, stdout=sp.DEVNULL, stderr=sp.DEVNULL)

        hw_repo_name = r['html_url'].rsplit("/")[-1]

        # open a new branch & checkout to that branch
        sp.run(['git', 'checkout', '-b', patch_branch],
               cwd=student_path/hw_repo_name, stdout=sp.DEVNULL, stderr=sp.DEVNULL)

        # copy file to student repo
        for f in changed_files.keys():
            (student_path/hw_repo_name/f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src=src_repo_path/f,
                            dst=student_path/hw_repo_name/f)
        for f in renamed_files.keys():
            os.remove(student_path/hw_repo_name/f)

        # changed_files = get_changed_files(
        #     master_commit = src_repo.heads['master'].commit,
        #     patch_commit = src_repo.heads[patch_branch].commit
        # )
        # push (publish) that branch to student repo
        sp.run(['git', 'add', '.'], cwd=student_path/hw_repo_name,
               stdout=sp.DEVNULL, stderr=sp.DEVNULL)

        # Pass if no changed
        student_repo = Repo(student_path/hw_repo_name)
        if len(student_repo.index.diff("HEAD")) == 0:
            spinner.text = pre_prompt_str + \
                f" {Back.GREEN}{Fore.BLACK} Passed {Style.RESET_ALL} Repo no change"
            spinner.succeed()
            continue

        sp.run(['git', 'commit', '-m', f':construction_worker: Patch: {patch_branch}'],
               cwd=student_path/hw_repo_name,
               stdout=sp.DEVNULL, stderr=sp.DEVNULL)

        spinner.text = pre_prompt_str + \
            f" {Fore.BLUE}publish patch to remote..{Fore.RESET}"
        res = sp.run(['git', 'push', '-u', 'origin', patch_branch], cwd=student_path/hw_repo_name,
                     stdout=sp.DEVNULL, stderr=sp.DEVNULL)
        if res.returncode != 0:
            spinner.text = (pre_prompt_str + f" {Back.RED}{Fore.BLACK} Failed {Style.RESET_ALL}"
                            + f" Cannot push branch {Fore.CYAN}{patch_branch}{Fore.RESET} to origin")
            spinner.fail()
            continue

        # open an pull-request on students repo
            # student_repo/patch-branch  -> student_repo/master
        body = {
            "title": f"[PATCH] {patch_branch}",
            "body": issue_tmpl_body,
            "head": patch_branch,
            "base": "master"
        }
        res = requests.post(f"https://api.github.com/repos/{org}/{r['name']}/pulls",
                            headers=github_headers(token), json=body)
        if res.status_code == 201:
            spinner.text = pre_prompt_str + \
                f" {Fore.BLACK}{Back.GREEN} Patched {Style.RESET_ALL}"
            spinner.succeed()
        else:
            spinner.text = (pre_prompt_str + f" {Back.RED}{Fore.BLACK} Failed {Style.RESET_ALL}"
                            + f" Cannot create PR {Fore.CYAN}{patch_branch}{Fore.RESET} to origin/master")
            spinner.fail()
            try:
                print(f"    {Fore.RED}{res.json()['errors'][0]['message']}")
            except:
                pass
            continue

    # TODO : print summary after patch
    #       how many success, skiped, failed
    pass


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
            if x.change_type == 'R':
                # file have been renamed, the dest file is include in the changed files
                # so we need to delete this file from dest repo

                # print(f'a remove(rename) :{x.a_blob.path}, type: {x.change_type}')
                renamed_files[x.a_blob.path] = {'type': x.change_type}
            else:
                # print(f'a change :{x.a_blob.path}, type: {x.change_type}')
                changed_files[x.a_blob.path] = {'type': x.change_type}

        # Change type of x is not 'delete'
        if x.b_blob is not None and x.b_blob.path not in changed_files.keys():
            # print(f'b change :{x.b_blob.path}, type: {x.change_type}')
            changed_files[x.b_blob.path] = {'type': x.change_type}

    return changed_files, renamed_files


if __name__ == "__main__":
    patch_project()
