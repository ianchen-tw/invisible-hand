from attr import attrs

from hand.api.github import GithubAPI
from hand.config import HandConfig

DEFAULT_SETTING = "<override>"


@attrs(auto_attribs=True, frozen=True)
class CheckResult:
    success: bool
    info: str = ""


@attrs(auto_attribs=True, frozen=True)
class DoCheck:
    """Automatically check environments"""

    # Checks
    gh_config_valid: bool = False
    google_client_secret_file_exist: bool = False
    git_cached: bool = False

    # Behavior arguments
    output_result: bool = False

    # TODO: add log
    def run(self, settings: HandConfig) -> CheckResult:
        """Start checking, will simply stop program if failed"""

        if self.gh_config_valid:
            token, org = settings.github.token, settings.github.org

            if token == DEFAULT_SETTING:
                return CheckResult(False, "You should update your gh_token")
            elif org == DEFAULT_SETTING:
                return CheckResult(False, "You should update your gh org")
            elif not GithubAPI(token=token, org=org).can_access_org():
                return CheckResult(False, "cannot access ORG!")

        if self.google_client_secret_file_exist:
            from pathlib import Path

            file_name = settings.google_spreadsheet.cred_filename

            if not Path(file_name).expanduser().exists():
                return CheckResult(False, "Google Sheet Client Secret File not exists")

        if self.git_cached:
            import subprocess as sp

            procs = sp.Popen(["git", "config", "credential.helper"], stdout=sp.PIPE)
            raw_data = procs.stdout.readline()
            data = raw_data.decode("utf-8").strip()
            if len(data) == 0:
                return CheckResult(False, "Git Credential not cached")

        return CheckResult(True)
