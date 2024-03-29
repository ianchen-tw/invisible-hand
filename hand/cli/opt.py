from typing import Final

from typer import Option

# opt_dry = typer.Option(False, "--dry", help="dry run, would not fire actual requests")

# opt_all_yes = typer.Option(False, "--yes", help="confirm to all", show_default=False)


# opt_github_token = typer.Option(
#     None, "--token", help="personalaccess token used in Github API",
# )

# opt_gh_org = typer.Option(None, "--org", help="sepcify target github organization",)


# Shared Options
class Opt:
    DRY: Final[bool] = Option(
        False, "--dry", help="dry run, would not fire actual requests"
    )
    ACCEPT_ALL: Final[bool] = Option(
        False, "--yes", help="confirm to all", show_default=False
    )
