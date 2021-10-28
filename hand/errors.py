import textwrap
from pprint import pformat
from typing import Dict, List, Optional

from .urls import url_for_issue


def format_paragraph(para: List[str]) -> str:
    result = ["\n\n"]
    for line in para:
        result += f"{line}\n"
    return textwrap.indent("".join(result), prefix=" " * 4)


class ERR_GOOGLE_CLIENT_SECRET_NOT_EXISTED(Exception):
    def __str__(self):
        exps = [
            "Didn't detect a `client_secret.json` file inside your cache folder",
            "If you already have it, use",
            "   `hand config copy-client <path-to-your-client-secret-file>",
            "to copy it into your cache folder",
            "",
            "If you don't know how to get this file, follow",
            "   https://pygsheets.readthedocs.io/en/stable/authorization.html",
            "to get your client_secret file, and follow the step above to copy it to the cache folder",
        ]
        return format_paragraph(exps)


class ERR_CHROME_DRIVER_NOT_INSTALLED(Exception):
    def __str__(self):
        exps = [
            "`chromedriver` not installed",
            "You need to install it before going further.",
            "If your'e using ubuntu, run:",
            "   `apt install chromium-chromedriver`",
            "For Mac users, run:",
            "   `brew cask install chromedriver`",
        ]
        return format_paragraph(exps)


class ERR_CONFIG_NOT_EXISTS(Exception):
    def __str__(self):
        return """
        Config not exists
        Use `hand config create` to create a new config file
        """


class ERR_UNIQUE_STUDENT_ID(Exception):
    def __init__(self, explanation: str, instances: List[Dict]):
        super().__init__(self)
        self.explanation: str = explanation
        self.instances: List[Dict] = instances

    def __str__(self):
        words = [self.explanation, pformat(self.instances)]
        return "\n".join(words)


class ERR_REQUIRE_NO_SPACE(Exception):
    def __init__(self, explanation: str, instances: List[str]):
        super().__init__(self)
        self.explanation: str = explanation
        self.instances: List[str] = instances

    def __str__(self):
        words = [self.explanation, pformat(self.instances)]
        return "\n".join(words)


class ERR_GIT_CREDENTIAL_HELPER_NOT_FOUND(Exception):
    def __str__(self):
        issue_git_cred = url_for_issue(issue_num=8)
        exps = [
            "Not detecting any credential helper inside git, use:",
            "   git config --global credential.helper cache",
            "before going any further.",
            "Or see:",
            f"  {issue_git_cred}",
            "for more information",
        ]
        return format_paragraph(exps)


class ERR_INVALID_GITHUB_TOKEN(Exception):
    def __init__(self, token: Optional[str] = None):
        self.token = token
        super().__init__(self)

    def __str__(self) -> str:
        exps = [
            "Invalid Github token" + (f": {self.token}." if self.token else ""),
            "Please update `github_config.ini`.",
        ]
        return format_paragraph(exps)


class ERR_CANNOT_FETCH_TEAM(Exception):
    def __init__(self, org: str, team_slug: str):
        self.org = org
        self.team = team_slug
        super().__init__(self, f"cannot fetch team: {self.org}/{self.team}")

    def __str__(self) -> str:
        exps = [
            "Cannot fetch team id",
            "Team info :",
            f"     org :{ self.org}",
            f"     team_slig :{ self.team}",
        ]
        return format_paragraph(exps)
