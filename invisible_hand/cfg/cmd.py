import typer
from .config_manager import ConfigManager

app = typer.Typer()

config_manager = ConfigManager()


@app.command()
def create():
    config_manager.create_default()
    typer.echo(f"Creating config file")


@app.command()
def edit():
    typer.echo(f"open config file for editing")


@app.command()
def remove():
    typer.echo(f"remove config file")
    config_manager.remove()


@app.command()
def path():
    typer.echo(f"show config file path")
