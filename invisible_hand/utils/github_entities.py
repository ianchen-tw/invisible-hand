import sys
from typing import Dict

import httpx
import requests
from requests.models import Response

from invisible_hand.config import app_context
from invisible_hand.errors import ERR_CANNOT_FETCH_TEAM
from .github_scanner import (
    get_github_endpoint,
    get_github_endpoint_paged_list,
    github_headers,
)


def main():
    print("nothin to run")


class DrySuccessResponse:
    def __init__(self, code: int):
        self.status_code: int = code
        self.dict: Dict = {}

    def set_dict(self, dict: Dict):
        """ Setup the dict returned by self.json() method
        """
        self.dict = dict.copy()

    def json(self):
        return self.dict


class Team:
    def __init__(self, org, team_slug="", github_token="", dry=False):
        self.info_sucess = False
        self.id = ""
        self.org = org
        self.team_slug = team_slug
        self.members = dict()
        self.github_token = github_token

        # Support dry run, would not fire any request
        self.dry = dry

        if not dry:
            self._get_members()

        # async
        self.httpx_headers = httpx.Headers(
            {
                "User-Agent": "GitHubClassroomUtils/1.0",
                "Authorization": "token " + github_token,
                # needed for the check-suites request
                "Accept": "application/vnd.github.antiope-preview+json",
            }
        )
        self.async_client = httpx.AsyncClient(headers=self.httpx_headers)

    def add_user_to_team(self, user_name) -> Response:
        if self.dry:
            return DrySuccessResponse(200)
        else:
            res = requests.put(
                "https://api.github.com/teams/{}/memberships/{}".format(
                    self.id, user_name
                ),
                headers=github_headers(self.github_token),
            )
            return res

    async def add_team_repository_async(self, repo, permission="pull") -> Response:
        """If permission=pull, it is equivalent to make this team subscribe to this repo"""
        if self.dry:
            return DrySuccessResponse(204)
        else:
            api_param = {"team_id": self.id, "owner": self.org, "repo": repo}
            # print(f'param: {api_param}')
            return await self.async_client.put(
                "https://api.github.com/teams/{team_id}/repos/{owner}/{repo}".format(
                    **api_param
                )
            )

    def get_memberships(self, user_name: str) -> Response:
        if self.dry:
            response = DrySuccessResponse(200)
            # state id either "pending" or "unknown"
            response.set_dict({"state": "unknown"})
            return response
        else:
            return requests.get(
                "https://api.github.com/teams/{}/memberships/{}".format(
                    self.id, user_name
                ),
                headers=github_headers(self.github_token),
            )

    def _require_team_id(func):
        def decorator(self):
            if self.id == "":
                self._get_team_id()
            func(self)

        return decorator

    @_require_team_id
    def _get_members(self):
        """ fetch remote and build self.members
        """
        try:
            res = get_github_endpoint_paged_list(
                endpoint=f"teams/{self.id}/members",
                github_token=self.github_token,
                verbose=False,
            )
        except:
            raise ERR_CANNOT_FETCH_TEAM(org=self.org, team_slug=self.team_slug)
        for user in res:
            self.members[user["login"]] = user
        # print(res)

    def _get_team_id(self):
        try:
            result = get_github_endpoint(
                "orgs/{}/teams/{}".format(self.org, self.team_slug),
                app_context.config.github.personal_access_token,
            )
        except:
            raise ERR_CANNOT_FETCH_TEAM(org=self.org, team_slug=self.team_slug)
            sys.exit(1)
        self.id = result["id"]


if __name__ == "__main__":
    main()
