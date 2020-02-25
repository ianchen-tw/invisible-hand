import sys
import shutil
import tempfile
import subprocess as sp
import string
import requests

from datetime import datetime
from pathlib import Path
from typing import List, Dict

import click
from colorama import init as colorama_init
from colorama import Fore, Back, Style
from halo import Halo

from ..config.github import config_github, config_announce_grade

from ..utils.github_scanner import get_github_endpoint_paged_list, github_headers
from ..utils.google_student import Gstudents

colorama_init()
spinner = Halo(stream=sys.stderr)

# We will use {source_repo}/{source_tmpl_issue} as the template to give students feedback

# The Pull request we made would fetch the first issue which has the same title
# as patch_branch to be the content


@click.command()
@click.argument('homework_prefix')
@click.option('--token', default=config_github['personal_access_token'], help="github access token")
@click.option('--org', default=config_github['organization'], show_default=True)
@click.option('--only-id', nargs=1, help="only id to announce")
@click.option('--feedback-source-repo', default=config_announce_grade['feedback_source_repo'], show_default=True)
def announce_grade(homework_prefix, token, org, only_id, feedback_source_repo):
    '''announce student grades to each hw repo'''
    student_feedback_title = f"Grade for {homework_prefix}"

    gstudents = Gstudents()
    feedbacks = gstudents.left_join(homework_prefix)

    # Clone feedback repo & set needed variables
    cur = Path('.')
    for d in cur.glob("feedback-tmp-*"):
        shutil.rmtree(d)
    spinner.info("delete dated folder")

    root_folder = Path(tempfile.mkdtemp(
        prefix="feedback-tmp-{}-".format(datetime.now().strftime("%b%d%H%M%S")), dir="."))
    spinner.succeed(
        f"Create tmp folder {Fore.YELLOW}{root_folder}{Style.RESET_ALL}")

    feedback_repo_path = root_folder / 'feedbacks'

    spinner.start(f"cloning feeback source repo : {feedback_source_repo}")
    sp.run(['git', 'clone',
            f'https://github.com/{org}/{feedback_source_repo}.git', feedback_repo_path.name, ], cwd=root_folder, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    spinner.succeed()

    hw_path = feedback_repo_path / homework_prefix / 'reports'

    for idx, feedback in enumerate(feedbacks, start=1):
        student_id = feedback['student_id']
        gh_handle = feedback['github_handle']
        if only_id != None and student_id != only_id:
            continue

        feedback['student_hw_repo'] = f'{homework_prefix}-{gh_handle}'
        pre_prompt_str = f"({idx}/{len(feedbacks)}) {Fore.YELLOW}{feedback['student_hw_repo']}{Fore.RESET}"

        # Get feedabck from feedback repo
        fb_path = hw_path/f"{student_id}.md"
        if not fb_path.exists():
            spinner.fail(f"{student_id}.md not exists")
            continue

        with open(fb_path, 'r') as fb:
            feedback_tmpl = string.Template(fb.read())
        feedback_body = feedback_tmpl.safe_substitute(feedback)

        # print('===========')
        # print(feedback_body)
        # print('===========')

        issue_request_body = {
            # feedback title
            "title": student_feedback_title,
            "body": feedback_body
        }

        existed_issue_number = None
        spinner.start(f"{pre_prompt_str} fetch issues...")
        try:
            issues = get_github_endpoint_paged_list(
                endpoint=f"repos/{org}/{feedback['student_hw_repo']}/issues",
                github_token=token, verbose=False, state='all')
        except:
            spinner.text = f"{pre_prompt_str} {Back.RED}{Fore.BLACK} Failed on fetch repo {Style.RESET_ALL}"
            spinner.fail()
            continue

        if len(issues) != 0:
            existed_issue_number = None
            try:
                issue = next(
                    i for i in issues if i['title'] == student_feedback_title)
                existed_issue_number = str(issue['number'])
            except:
                existed_issue_number = None
        # spinner.info(f'edit issue number:{existed_issue_number}')
        args = {
            'pre_prompt_str': pre_prompt_str,
            'owner': org,
            'repo': feedback['student_hw_repo'],
            'headers': github_headers(token),
            'json_body': issue_request_body
        }
        if existed_issue_number != None:
            args['issue_number'] = existed_issue_number
            args['json_body']['state'] = "open"
            edit_issue(**args)
        else:
            create_issue(**args)


def edit_issue(pre_prompt_str="", owner="", repo="", headers=None, json_body="", issue_number=""):
    res = requests.patch(
        f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}", headers=headers, json=json_body)
    if res.status_code == 200:
        spinner.text = pre_prompt_str + \
            f" {Fore.BLACK}{Back.GREEN} Delivered {Style.RESET_ALL}"
        spinner.succeed()
    else:
        spinner.text = (pre_prompt_str + f" {Back.RED}{Fore.BLACK} Failed {Style.RESET_ALL}"
                        + f" Cannot edit issue in {Fore.CYAN}{repo}{Fore.RESET}")
        spinner.fail()
        try:
            print(f"    {Fore.RED}{res.json()['errors'][0]['message']}")
        except:
            pass


def create_issue(pre_prompt_str="", owner="", repo="", headers=None, json_body=""):
    res = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/issues", headers=headers, json=json_body)
    if res.status_code == 201:
        spinner.text = pre_prompt_str + \
            f" {Fore.BLACK}{Back.GREEN} Delivered {Style.RESET_ALL}"
        spinner.succeed()
    else:
        spinner.text = (pre_prompt_str + f" {Back.RED}{Fore.BLACK} Failed {Style.RESET_ALL}"
                        + f" Cannot create issue to {Fore.CYAN}{repo}{Fore.RESET}")
        spinner.fail()
        try:
            print(f"    {Fore.RED}{res.json()['errors'][0]['message']}")
        except:
            pass


if __name__ == "__main__":
    announce_grade()
