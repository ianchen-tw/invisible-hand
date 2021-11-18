from attr import attrs


@attrs(auto_attribs=True, frozen=True)
class DoCheck:
    """Automatically check environments"""

    gh_config_valid: bool = False
    google_client_secret_file_exist: bool = False
    git_cached: bool = False

    def run(self):
        """Start checking, will simply stop program if failed"""
        if self.gh_config_valid:
            print("check gh_config_valid")
            print("check org name")
            print("check token valid")

        if self.google_client_secret_file_exist:
            pass
            # ensure_client_secret_json_exists()
        if self.git_cached:
            print("check git cached")
            # ensure_git_cached()
