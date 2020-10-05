import subprocess as sp
import httpx
from invisible_hand.errors import (
    ERR_GIT_CREDENTIAL_HELPER_NOT_FOUND, ERR_INVALID_GITHUB_TOKEN)


def ensure_git_cached():
    """Would raise GIT_CREDENTIAL_HELPER_NOT_FOUND if git credential not being cached/stored. """
    # detect credential.helper
    procs = sp.Popen(['git', 'config', 'credential.helper'], stdout=sp.PIPE)
    raw_data = procs.stdout.readline()
    data = raw_data.decode('utf-8').strip()
    if len(data) == 0:
        raise ERR_GIT_CREDENTIAL_HELPER_NOT_FOUND


def ensure_gh_token(token: str):
    """
    Raise token error if token is valid by requesting github
    """
    httpx_headers = httpx.Headers({
        "User-Agent": "GitHubClassroomUtils/1.0",
        "Authorization": f"token {token}",
    })
    res = httpx.get(f"https://api.github.com/user", headers=httpx_headers)
    if res.status_code != 200:
        raise ERR_INVALID_GITHUB_TOKEN(token=token)
