# github_event_times.py
# Dan Wallach <dwallach@rice.edu>
# Available subject to the Apache 2.0 License
# https://www.apache.org/licenses/LICENSE-2.0

#import argparse
import click
from pprint import pprint
from datetime import datetime, timedelta
import re
import sys
from pathlib import Path
from typing import List, NamedTuple, Tuple

from halo import Halo
from tabulate import tabulate

from ..config.github import config_github, config_event_times

from ..utils.github_scanner import LOCAL_TIMEZONE
from ..utils.github_scanner import *
from ..utils.github_entities import Team
from ..ensures import ensure_gh_token


def is_deadline_passed(dl: datetime, submit: datetime) -> Tuple[bool, timedelta]:
    dl = dl.astimezone(submit.tzinfo)
    if dl < submit:
        return True, submit - dl
    else:
        return False, dl-submit


class commitInfo(NamedTuple):
    commit_hash: str  # 7 characters hash value
    pushed_time: str
    msg: str
    repo: str


class GitHubRepoInfo(NamedTuple):
    name: str
    commit_hash: str  # 7 characters hash value

# python3 github_event_times.py hw0-ianre657:cb75e99


@click.command()
@click.argument('input-file')
@click.option('--token', default=config_github['personal_access_token'], help="github access token")
@click.option('--org', default=config_github['organization'], show_default=True)
@click.option('--deadline', default=config_event_times['deadline'], show_default=True,
              help='deadline format: "yyyy-mm-dd" or any ISO8601 format string (timezone will be set to local timezone)')
@click.option('--target-team', default=None, help="specific team to operate on")
def event_times(input_file, org, token, deadline, target_team):
    '''
    input-file: file contains list of repo-hash.

    repo-hash : string in <repo>:<hash> format
            hw0-ianre657:cb75e99
    '''
    global github_organization
    global github_token

    try:
        parsed_repos = get_repo_infos(input_file)
    except FileNotFoundError as e:
        print(str(e))
        return
    ensure_gh_token(token)
    spinner = Halo(stream=sys.stderr)

    github_organization = org
    github_token = token

    print(f'deadline: {deadline}')

    submit_deadline = iso8601.parse_date(deadline)
    submit_deadline = submit_deadline.replace(tzinfo=LOCAL_TIMEZONE)

    spinner.info(f"Deadline : {submit_deadline}")
    success_group = []
    fail_group = []
    spinner.start("Start to check late submissions")

    # get team membershup info
    if target_team is not None:
        only_team_members = set(Team(
            org=github_organization, team_slug=target_team, github_token=github_token).members.keys())

    for idx, repo in enumerate(parsed_repos, start=1):
        #print("get commit time for {}".format(repo))
        if target_team is not None:
            import re
            user_id = re.sub('hw[\d]+-', '', repo.name)
            # print(f'user_id :{user_id}')
            if user_id not in only_team_members:
                continue
        spinner.text = f"({idx}/{len(parsed_repos)}) Checking {repo.name}"
        result = getRepoCommitTime(
            org=github_organization, repo=repo.name, commit_hash=repo.commit_hash)
        for r in result:
            # print(r)
            passed, delta = is_deadline_passed(
                submit_deadline, iso8601.parse_date(r.pushed_time))
            if passed:
                fail_group.append({
                    'repo-name': r.repo,
                    'commit-hash': r.commit_hash,
                    'time-passed': delta,
                    'last-pushtime': r.pushed_time
                })
            else:
                success_group.append((r, delta))
                #print(f'{r}: {delta} later')
    spinner.succeed("Check finished")
    print('='*20, 'REPORT', '='*20)
    print(f'Total submissions : {len(parsed_repos)}')
    print(f'late submissions: {len(fail_group)}')
    print(f'Submission Deadline: {submit_deadline}')
    print(tabulate(fail_group, headers="keys"))


def get_repo_infos(filename: str) -> List[GitHubRepoInfo]:
    st = Path(filename).read_text()
    infos = st.split()
    result = []
    for r in infos:
        repo, commit_hash = r.split(":")
        result.append(GitHubRepoInfo(repo, commit_hash))
    return result


def getRepoCommitTime(org: str, repo: str, commit_hash: str) -> List[commitInfo]:
    global github_token
    response = get_github_endpoint_paged_list(
        f"repos/{org}/{repo}/events", github_token, verbose=False)
    event_list = [x for x in response if x['type'] == 'PushEvent']
    # find the localtiome of the given commit SHA that is pushed.
    msgs = []
    for event in event_list:
        try:
            github_id = event['actor']['login']
            date = localtime_from_iso_datestr(event['created_at'])
            target_commits = [x for x in event['payload']
                              ['commits'] if x['sha'][0:7] == commit_hash]

            if len(target_commits) == 0:
                continue
            elif len(target_commits) >= 2:
                print("SHA Conflict for user: {}".format(github_id))
            else:
                target_commit = target_commits[0]

                commit_message = tex_escape(target_commit['message'].splitlines()[
                                            0])  # only the first line if multiline
                commit_hash = target_commit['sha'][0:7]

                result = commitInfo(commit_hash, date, commit_message, repo)
                # result_str = "{} sha:{}, msg:{}, date:{}".format(github_id, commit_hash, commit_message, date)
                msgs.append(result)
        except KeyError:
            print("Error: malformed event!")
            pprint(event)
    return msgs

# https://stackoverflow.com/questions/16259923/how-can-i-escape-latex-special-characters-inside-django-templates


def tex_escape(text: str) -> str:
    """
        :param text: a plain text message
        :return: the message escaped to appear correctly in LaTeX
    """
    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    regex = re.compile('|'.join(re.escape(str(key))
                                for key in sorted(conv.keys(), key=lambda item: - len(item))))
    return regex.sub(lambda match: conv[match.group()], text)


if __name__ == "__main__":
    event_times()
