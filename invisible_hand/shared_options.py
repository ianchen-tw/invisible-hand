import typer

from .config.github import config_github

opt_dry = typer.Option(False, "--dry", help="dry run, would not fire actual requests")

opt_github_token = typer.Option(
    config_github["personal_access_token"],
    "--token",
    help="personalaccess token used in Github API",
    show_default=False,
)

opt_gh_org = typer.Option(
    config_github["organization"], "--org", help="sepcify target github organization",
)
