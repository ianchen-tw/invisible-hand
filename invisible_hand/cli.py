from typing import Optional

import typer
from pydantic.error_wrappers import ValidationError

from .config import app as config_typer
from .config import app_context
from .scripts import (
    add_students,
    announce_grade,
    crawl_classroom,
    event_times,
    grant_read_access,
    patch_project,
)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
app = typer.Typer(
    context_settings=CONTEXT_SETTINGS,
    help="Manage your classroom under Github organization.",
)


@app.callback()
def main(
    custom_base: Optional[str] = typer.Option(
        None, "--custom-base", help="Use custom base folder for configs"
    )
):
    config_manager = app_context.config_manager

    if custom_base:
        config_manager.change_base_folder(custom_base)
        typer.echo(f"Using custom base-folder: {config_manager.get_base_path()}")

    # populate actual config
    if config_manager.config_path.exists():
        try:
            app_context.config = config_manager.read_config()
        except ValidationError:
            typer.echo("[Warning] Corrupted config file")


app.command("add-students")(add_students)
app.command("grant-read-access")(grant_read_access)
app.command("event-times")(event_times)
app.command("patch-project")(patch_project)
app.command("crawl-classroom")(crawl_classroom)
app.command("announce-grade")(announce_grade)

app.add_typer(config_typer, name="config")
