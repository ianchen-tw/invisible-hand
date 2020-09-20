import sys
import requests
import asyncio
import trio
import httpx

from typing import List

from requests.models import Response

from halo import Halo

from ..core.color_text import warn
from ..config.github import config_github
from .github_scanner import get_github_endpoint, github_headers, get_github_endpoint_paged_list


def main():
    print("nothin to run")


class Team:
    def __init__(self, org, team_slug="", github_token=""):
        self.info_sucess = False
        self.id = ""
        self.org = org
        self.team_slug = team_slug
        self.members = dict()
        self.github_token = github_token
        self._get_members()

        # async
        self.httpx_headers = httpx.Headers({
            "User-Agent": "GitHubClassroomUtils/1.0",
            "Authorization": "token " + github_token,
            # needed for the check-suites request
            "Accept": "application/vnd.github.antiope-preview+json"
        })
        self.async_client = httpx.AsyncClient(headers=self.httpx_headers)

    def add_user_to_team(self, user_name) -> Response:
        res = requests.put(
            "https://api.github.com/teams/{}/memberships/{}".format(
                self.id, user_name),
            headers=github_headers(self.github_token)
        )
        return res

    def add_team_repository(self, repo, permission="pull") -> Response:
        '''If permission=pull, it is equivalent to make this team subscribe to this repo 
        '''
        api_param = {
            'team_id': self.id,
            'owner': self.org,
            'repo': repo
        }
        return requests.put("https://api.github.com/teams/{team_id}/repos/{owner}/{repo}".format(**api_param),
                            headers=github_headers(self.github_token))

    async def add_team_repository_async(self, repo, permission="pull") -> Response:
        '''If permission=pull, it is equivalent to make this team subscribe to this repo 
        '''
        api_param = {
            'team_id': self.id,
            'owner': self.org,
            'repo': repo
        }
        # print(f'param: {api_param}')
        return await self.async_client.put("https://api.github.com/teams/{team_id}/repos/{owner}/{repo}".format(**api_param))

    def get_memberships(self, user_name: str) -> Response:
        return requests.get("https://api.github.com/teams/{}/memberships/{}".format(self.id, user_name),
                            headers=github_headers(self.github_token))

    def _require_team_id(func):
        def decorator(self):
            if self.id == "":
                self._get_team_id()
            func(self)
        return decorator

    @_require_team_id
    def _get_members(self):
        try:
            # res = get_github_endpoint(
            #     endpoint="teams/{}/members".format(self.id),
            #     github_token=self.github_token,
            # )
            res = get_github_endpoint_paged_list(
                endpoint="teams/{}/members".format(self.id),
                github_token=self.github_token,
                verbose=False
            )
        except:
            prompt_cannot_fetch_team(org=self.org, team_slug=self.team_slug)
            sys.exit(1)
        for user in res:
            self.members[user['login']] = user
        # print(res)

    def _get_team_id(self):
        try:
            result = get_github_endpoint(
                "orgs/{}/teams/{}".format(self.org, self.team_slug),
                config_github['personal_access_token'],
            )
        except:
            prompt_cannot_fetch_team(org=self.org, team_slug=self.team_slug)
            sys.exit(1)
        self.id = result['id']


def prompt_cannot_fetch_team(org: str, team_slug: str):
    print(warn.txt("Cannot fetch team id").to_str)
    print("Team info:")
    print(f"    org: {org}")
    print(f"    team_slug: {team_slug}")


if __name__ == "__main__":
    main()
