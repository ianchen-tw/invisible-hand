from typing import Dict, List

from attr import attrib, attrs

from hand.api.github import GithubAPI
from ._protocol import Script


def unique(arr: List[str]) -> List[str]:
    return list(set(arr))


@attrs(auto_attribs=True, frozen=True)
class PropsScriptAddStudents:
    dry_run: bool = True
    all_yes: bool = False


@attrs(auto_attribs=True, frozen=True)
class InviteRequest:
    user_handle: str


@attrs(auto_attribs=True)
class TeamInviteExecutor:
    """Actual implementer of invite
        Would only fires number of result
    """

    gh_api: GithubAPI

    def submit(self, request: InviteRequest):
        pass

    def start(self) -> Dict[str, str]:
        pass


@attrs(auto_attribs=True)
class ScriptAddStudents(Script):
    gh_invite_team: str
    user_handles: List[str] = attrib(converter=unique)
    dry_run: bool

    def run(self):
        self.step_get_team_members()

        invalids = self.step_check_invalid_handles()
        to_invite = list(set(self.user_handles) - set(invalids))

        self.step_invite_students(to_invite)

    def step_get_team_members(self) -> List[str]:
        print("step_get_team_members")

    def step_check_invalid_handles(self) -> List[str]:
        print("step_check_invalid_handles")
        return []

    def step_invite_students(self, to_invite: List[str]):
        pass
