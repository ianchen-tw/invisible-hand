from typing import Any, Dict, Optional

import httpx
from attr import attrs

QL_ENDPOINT = "https://api.github.com/graphql"


@attrs(auto_attribs=True)
class GithubAPI:
    token: str
    org: str

    def can_access_org(self) -> bool:
        """Verify if current user can get access to org with token"""
        client = get_client(self.token)
        result = viewerIsOrgMember(client, org=self.org)
        return result if result is not None else False

    def invite_user_to_team(self, team_slug: str, user: str) -> bool:
        # TODO
        return False

    # async def is_user_in_team(self, user: str, team: str) -> bool:
    #     pass

    # async def is_valid_user(self) -> bool:
    #     pass

    # async def get_team_members(self) -> List[str]:
    #     pass

    # async def invite_user_to_team(self, user: str, team: str):
    #     pass


def get_client(token):
    return httpx.Client(
        headers=httpx.Headers(
            {
                "User-Agent": "GitHubClassroomUtils/1.0",
                "Authorization": f"token {token}",
            }
        )
    )


# Queries


def viewerIsOrgMember(client: httpx.Client, org: str) -> Optional[bool]:
    ql = """query($org: String!){
                organization(login:$org){
                    viewerIsAMember
                }
        }"""
    result = client.post(QL_ENDPOINT, json={"query": ql, "variables": {"org": org}})

    if result.status_code == 200:
        body: Dict = result.json()
        if body.get("errors", None) is not None:
            print(body["errors"])
            return False
        else:
            org: Dict[str, Any] = body["data"]["organization"]
            return org["viewerIsAMember"]
    return None
