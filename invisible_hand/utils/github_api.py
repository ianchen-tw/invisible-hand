import httpx
from ..core.color_text import warn


class InvalidGithubTokenException(Exception):
    def __init__(self, token: str):
        self.token = token
        super().__init__(self, f'Invalid token: {token}')

    def __str__(self) -> str:
        words = warn.newline() \
            + warn.txt('Invalid Github token:').kw(f' {self.token}').newline() \
            + warn.txt('please update ').kw2('github_config.ini').newline()
        return str(words)


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
        raise InvalidGithubTokenException(token=token)
