import os
from pathlib import Path
from shutil import copy2, which

import typer
from pydantic import ValidationError

from .config_manager import ConfigManager
from .context import app_context
from .words import STR_CFG_IS_VALID, STR_CFG_NOT_EXISTS

manager: ConfigManager

app = typer.Typer(help="Config File utilities")


@app.callback()
def setup_manager():
    global manager
    manager = app_context.config_manager


@app.command()
def create():
    """Create config file"""
    global manager

    config_path = manager.config_path
    if not manager.config_path.exists():
        manager.create_default()
        typer.echo(f"Config file created: {config_path}")
        raise typer.Exit(0)

    override = typer.confirm("Config file exists, override it?")
    if not override:
        raise typer.Abort()
    manager.create_default()
    typer.echo(f"Config file created: {config_path}")
    raise typer.Exit(0)


@app.command("copy-client-secret")
def copy_client_secret(
    src_path: Path = typer.Argument(
        default=..., metavar="📁file", help="Path to your client_secret file"
    ),
):
    """Copy client_secret.json to cache folder"""
    global manager
    dst_path = manager.google_client_secret_path
    if not src_path.exists():
        typer.echo(f"File not exists: {src_path}")
        typer.Abort()
    copy2(src_path, dst_path)
    typer.echo(f"Copy file:{src_path} to {dst_path}")


@app.command()
def check():
    """Check if your config file is valid & usable"""
    global manager

    if not manager.config_path.exists():
        typer.echo(STR_CFG_NOT_EXISTS)
        raise typer.Exit(1)

    try:
        _ = manager.read_config()
    except ValidationError as e:
        typer.echo(e)
        typer.echo(f"please check your config file: {manager.config_path}")
        raise typer.Abort()

    typer.echo(STR_CFG_IS_VALID)
    raise typer.Exit(0)


@app.command()
def edit(editor: str = os.getenv("EDITOR", default="code")):
    """Open config file"""
    global manager
    if which(editor) is not None:
        os.system(f"{editor} {manager.config_path}")
    else:
        typer.echo("Please specify a valid editor to open the file")
        raise typer.Abort()


@app.command()
def remove(
    yes: bool = typer.Option(False, "--yes", help="confirm to remove", show_default=False)
):
    """Remove related data completely"""
    global manager
    base_path: Path = manager.get_base_path().resolve()
    confirm = yes or typer.confirm(f"Remove folder : {base_path}?")
    if not confirm:
        typer.echo("Not Removing")
        raise typer.Abort()
    manager.remove()
    typer.echo(f"Folder Removed: {base_path}")


@app.command()
def path():
    """Get the folder for configs"""
    global manager
    base_path: Path = manager.get_base_path().resolve()
    typer.echo(base_path)
