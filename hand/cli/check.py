from typing import Optional

from attr import define

from hand.api.github import GithubAPI
from hand.config import HandConfig

DEFAULT_SETTING = "<override>"


@define(frozen=True)
class CheckResult:
    success: bool
    info: str = ""


@define(frozen=True)
class CheckOptions:
    # Checks
    gh_config_valid: bool
    google_client_secret_file_exist: bool
    git_cached: bool


class DoCheck:
    """Automatically check environments"""

    def __init__(self, settings: HandConfig, output_result: bool = False):
        self._config = settings
        self._opt: Optional[CheckOptions] = None
        self._output_result: bool = output_result

        # public accessable
        token, org = self._config.github.token, self._config.github.org
        self.gh_api = GithubAPI(token=token, org=org)

    def withOptions(
        self,
        gh_config_valid: bool = False,
        google_client_secret_file_exist: bool = False,
        git_cached: bool = False,
    ) -> "DoCheck":
        opt = CheckOptions(
            gh_config_valid=gh_config_valid,
            google_client_secret_file_exist=google_client_secret_file_exist,
            git_cached=git_cached,
        )
        self._opt = opt
        return self

    # TODO: add log
    def run(self) -> CheckResult:
        """Start checking, will simply stop program if failed"""

        if self._opt.gh_config_valid:
            token, org = self._config.github.token, self._config.github.org

            if token == DEFAULT_SETTING:
                return CheckResult(False, "DoCheck: You should update your gh_token")
            elif org == DEFAULT_SETTING:
                return CheckResult(False, "DoCheck: You should update your gh org")
            elif not self.gh_api.can_access_org():
                return CheckResult(False, "DoCheck: cannot access ORG!")

        if self._opt.google_client_secret_file_exist:
            from pathlib import Path

            file_name = self._config.google_spreadsheet.cred_filename

            if not Path(file_name).expanduser().exists():
                return CheckResult(False, "Google Sheet Client Secret File not exists")

        if self._opt.git_cached:
            import subprocess as sp

            procs = sp.Popen(["git", "config", "credential.helper"], stdout=sp.PIPE)
            raw_data = procs.stdout.readline()
            data = raw_data.decode("utf-8").strip()
            if len(data) == 0:
                return CheckResult(False, "Git Credential not cached")

        return CheckResult(True)
