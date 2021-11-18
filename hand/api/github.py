from typing import List

from attr import attrs


@attrs(auto_attribs=True)
class GithubAPI:
    token: str
    org: str

    async def is_user_in_team(self, user: str, team: str) -> bool:
        pass

    async def is_valid_user(self) -> bool:
        pass

    async def get_team_members(self) -> List[str]:
        pass

    async def invite_user_to_team(self, user: str, team: str):
        pass
