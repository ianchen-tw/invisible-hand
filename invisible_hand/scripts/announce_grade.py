import shutil
import string
import subprocess as sp
import sys
import tempfile
from datetime import datetime
from functools import wraps
from pathlib import Path
from pprint import pprint
from time import time
from typing import Dict, List, Optional

import httpx
import trio
import typer
from halo import Halo

from invisible_hand.config import app_context
from ..ensures import ensure_config_exists, ensure_gh_token
from ..utils.github_scanner import get_github_endpoint_paged_list_async
from ..utils.google_student import Gstudents
from .shared_options import opt_all_yes, opt_gh_org, opt_github_token

# We will use {source_repo}/{source_tmpl_issue} as the template to give students feedback

# The Pull request we made would fetch the first issue which has the same title
# as patch_branch to be the content


def measure_time(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        return result, te - ts

    return wrap


def announce_grade(
    homework_prefix: str = typer.Argument(..., help="prefix of the target homework"),
    feedback_source_repo: Optional[str] = typer.Option(
        None, show_default=True, help="Repo contains students' feedbacks"
    ),
    only_id: Optional[str] = typer.Option(default=None, help="only id to announce"),
    token: Optional[str] = opt_github_token,
    org: str = opt_gh_org,
    dry: str = typer.Option(
        False, "--dry", help="dry run, do not publish result to the remote"
    ),
    yes: bool = opt_all_yes,
):
    """Announce student grades to each hw repo"""
    ensure_config_exists()

    def fallback(val, fallback_value):
        return val if val else fallback_value

    # Handle default value manually because we'll change our config after app starts up
    token: str = fallback(token, app_context.config.github.personal_access_token)
    org: str = fallback(org, app_context.config.github.organization)
    feedback_source_repo: str = fallback(
        feedback_source_repo, app_context.config.announce_grade.feedback_source_repo
    )

    ensure_gh_token(token)
    if not (yes or typer.confirm(f"Add annouce_grade to {org}/{homework_prefix}?")):
        raise typer.Abort()

    # TODO: use logging lib to log messages
    spinner = Halo(stream=sys.stderr)

    student_feedback_title = f"Grade for {homework_prefix}"

    gstudents = Gstudents()
    feedback_vars = gstudents.left_join(homework_prefix)

    # Clone feedback repo & set needed variables
    cur = Path(".")

    for d in cur.glob("feedback-tmp-*"):
        shutil.rmtree(d)
    spinner.info("delete dated folder")

    root_folder = Path(
        tempfile.mkdtemp(
            prefix="feedback-tmp-{}-".format(datetime.now().strftime("%b%d%H%M%S")),
            dir=".",
        )
    )
    spinner.succeed(f"Create tmp folder {root_folder}")

    feedback_repo_path = root_folder / "feedbacks"

    spinner.info(f"cloning feeback source repo : {feedback_source_repo}")
    _, t = measure_time(sp.run)(
        [
            "git",
            "clone",
            f"https://github.com/{org}/{feedback_source_repo}.git",
            feedback_repo_path.name,
        ],
        cwd=root_folder,
    )
    spinner.succeed(
        f"cloning feeback source repo : {feedback_source_repo} ... {t:4.2f} sec"
    )
    client = httpx.AsyncClient(
        headers=httpx.Headers(
            {
                "User-Agent": "GitHubClassroomUtils/1.0",
                "Authorization": "token " + token,
                # needed for the check-suites request
                "Accept": "application/vnd.github.antiope-preview+json",
            }
        )
    )

    hw_path = feedback_repo_path / homework_prefix / "reports"

    # generate feedbacks
    fbs, t = measure_time(gen_feedbacks)(homework_prefix, hw_path, feedback_vars)
    spinner.succeed(f"Generate content for feedbacks ... {t:5.3f} sec")

    # handle only_id
    if only_id:
        try:
            # detect possible buggy condition
            info = gstudents.get_student(only_id)
        except RuntimeError as e:
            print(" *=" * 30)
            print("Warning!")
            print(e)
            return
        only_repo_name = get_hw_repo_name(homework_prefix, info["github_handle"])
        fbs = list(filter(lambda fb: fb["repo_name"] == only_repo_name, fbs))

    async def push_to_remote(feedback_title, feedbacks):
        # push to remote
        async def push_feedback(fb):
            request_body = {"title": feedback_title, "body": fb["value"]}
            try:
                issue_num = await find_existing_issue(
                    client, org, fb["repo_name"], feedback_title
                )
            except BaseException:
                print(f'error on {fb["repo_name"]}')
                return
            if issue_num:
                request_body["state"] = "open"  # reopen issue
                url = f"https://api.github.com/repos/{org}/{fb['repo_name']}/issues/{issue_num}"
                await edit_issue_async(client, url, issue_num, request_body)
            else:
                url = f"https://api.github.com/repos/{org}/{fb['repo_name']}/issues"
                await create_issue_async(client, url, request_body)
            print(f'success {fb["repo_name"]}')

        async with trio.open_nursery() as nursery:
            for fb in feedbacks:
                nursery.start_soon(push_feedback, fb)

    # print out target repos
    print("repo to announce grade:")
    pprint([fb["repo_name"] for fb in fbs])

    if dry:
        spinner.succeed("DRYRUN: skip push to remote")
    else:
        if typer.confirm("Do you want to continue?", default=False):
            _, t = measure_time(trio.run)(push_to_remote, student_feedback_title, fbs)
            spinner.succeed(f"Push feedbacks to remote ... {t:5.2f} sec")
        else:
            spinner.warn("You refused to publish to remote")

    spinner.succeed("finished announce grade")
    return


def get_hw_repo_name(hw_prefix, gh_handle):
    return f"{hw_prefix}-{gh_handle}"


def gen_feedbacks(hw_prefix, fb_root_path, fb_vars) -> List[Dict]:
    # substitude with template info
    result = []
    for vars in fb_vars:
        feedback = {"repo_name": None, "value": None}
        # generate names for student h.w. repos
        student_id, handle = vars["student_id"], vars["github_handle"]
        repo_name = get_hw_repo_name(hw_prefix, handle)
        feedback["repo_name"] = repo_name
        # fetch each students feedback template file by id
        fb_tmpl_file = fb_root_path / f"{student_id}.md"
        if fb_tmpl_file.exists():
            # substitude value inside feedback template
            with open(fb_tmpl_file, "r") as tmpl_file:
                fb_tmpl = string.Template(tmpl_file.read())
                feedback["value"] = fb_tmpl.safe_substitute(vars)

        if feedback["repo_name"] and feedback["value"]:
            result.append(feedback)
    return result


async def find_existing_issue(client, org, repo_name, issue_title) -> Optional[int]:
    # TODO: remove argument: org
    # print(f'finding existing issue... :{repo_name}/{issue_title}')
    issues = await get_github_endpoint_paged_list_async(
        client, f"repos/{org}/{repo_name}/issues", state="all"
    )
    # TODO: deal with repo not exist case
    if len(issues) != 0:
        try:
            issue = next(i for i in issues if i["title"] == issue_title)
            return int(issue["number"])
        except:
            pass
    return None


async def edit_issue_async(client, url, issue_number, requst_body):
    res = await client.patch(url, json=requst_body)
    if res.status_code != 200:
        print(f"failed on editing issue: {url}")
        try:
            print(f"{res.json()['errors'][0]['message']}")
        except:
            pass


async def create_issue_async(client, url, request_body):
    res = await client.post(url, json=request_body)
    if res.status_code != 201:
        print(f"failed on {url}")
        try:
            print(f"{res.json()['errors'][0]['message']}")
        except:
            pass


if __name__ == "__main__":
    announce_grade()
