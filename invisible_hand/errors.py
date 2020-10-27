from typing import Optional

from .core.color_text import warn
from .urls import url_for_issue


class ERR_GIT_CREDENTIAL_HELPER_NOT_FOUND(Exception):
    def __init__(self):
        super().__init__(self)

    def _get_git_cred_warning(self):
        def ljust(word, leng):
            return "{0:<{1}}".format(word, leng)

        leng = 65
        words = (
            warn.newline()
            .txt(ljust(" Not detect any credential helper inside git, use: ", leng))
            .newline()
            + warn.kw(
                ljust("  git config --global credential.helper cache", leng)
            ).newline()
            + warn.txt(ljust(" before going any further.", leng)).newline()
            + warn.txt(" Or see: ")
            + warn.kw2(f" {url_for_issue(issue_num=8)}   ").newline()
            + warn.txt(ljust(" for more information", leng))
            + warn.newline()
        )
        return words.to_str()

    def __str__(self):
        return self._get_git_cred_warning()


class ERR_INVALID_GITHUB_TOKEN(Exception):
    def __init__(self, token: Optional[str] = None):
        self.token = token
        info = "Invalud token" + f": {token}" if token else ""
        super().__init__(self, info)

    def __str__(self) -> str:
        if self.token:
            words = (
                warn.newline()
                + warn.txt(" Invalid Github token:").kw(f" {self.token} ").newline()
                + warn.txt(" please update ").kw2("github_config.ini").newline()
            )
        else:
            words = (
                warn.newline()
                + warn.txt(" Invalid Github token ").newline()
                + warn.txt(" please update ").kw2("github_config.ini ").newline()
            )
        return str(words)
