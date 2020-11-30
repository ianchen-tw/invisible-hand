from pprint import pformat
from typing import Dict, List, Optional
from invisible_hand import console
from .core.console_color import kw, danger
from .urls import url_for_issue


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
    def __init__(self):
        super().__init__(self)

    def __str__(self):
        issue_git_cred = url_for_issue(issue_num=8)
        with console.capture() as capture:
            console.print()
            console.print("[red]Not detect any credential helper inside git[/red], use:")
            console.print(" [blue]git config --global credential.helper cache[/blue]")
            console.print("before going any further.")
            console.print("Or see:")
            console.print(
                f"  [link={issue_git_cred}][blue]{issue_git_cred}[/blue][/link]",
            )
            console.print("for more information")
        return capture.get()


class ERR_INVALID_GITHUB_TOKEN(Exception):
    def __init__(self, token: Optional[str] = None):
        self.token = token
        info = "Invalid token" + f": {token}" if token else ""
        super().__init__(self, info)

    def __str__(self) -> str:
        with console.capture() as capture:
            console.print("\n")
            console.print(f"Invalid Github token", end="")
            console.print(f": [blue]{self.token}[/blue]" if self.token else "")
            console.print("please update [blue]github_config.ini[/blue]")
        return capture.get()


class ERR_CANNOT_FETCH_TEAM(Exception):
    def __init__(self, org: str, team_slug: str):
        self.org = org
        self.team = team_slug
        super().__init__(self, f"cannot fetch team: {self.org}/{self.team}")

    def __str__(self) -> str:
        with console.capture() as capture:
            console.print("\n")
            console.print(danger("Cannot fetch team id"))
            console.print("Team info :")
            console.print(f"     org : {kw(self.org)}")
            console.print(f"     team_slug: {kw(self.team)}")
        return capture.get()

