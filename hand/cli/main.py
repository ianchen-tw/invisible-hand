import typer

# from .cmd_config import app as cmd_config_app


app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Manage your classroom under Github organization.",
)

from .cmd import (
    add_students,
    check_env,
    crawl_classroom,
    event_times,
    grant_read_access,
    patch_project,
    publish_grade,
)

app.command(name="add")(add_students)
app.command(name="grant")(grant_read_access)
app.command(name="patch")(patch_project)
app.command(name="crawl")(crawl_classroom)
app.command(name="times")(event_times)
app.command(name="publish")(publish_grade)
app.command(name="check")(check_env)
