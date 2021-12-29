from typing import List

from attr import attrib, attrs

from hand.api.github import GithubAPI
from ._protocol import Script


def unique(arr: List[str]) -> List[str]:
    return list(set(arr))


@attrs(auto_attribs=True)
class ScriptAddStudents(Script):
    gh_invite_team: str
    user_handles: List[str] = attrib(converter=unique)
    dry_run: bool
    gh_api: GithubAPI

    def run(self):
        """The main script executing function"""
        self.step_invite_students(to_invite=self.user_handles)

    def step_invite_students(self, to_invite: List[str]):
        for user in to_invite:
            # Announce
            ...
            # Execute
            if not self.dry_run:
                self.gh_api.invite_user_to_team(
                    team_slug=self.gh_invite_team, user=user
                )
            # Show Result
            ...
