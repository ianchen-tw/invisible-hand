# import click


# from .scripts.add_students import add_students
# from .scripts.announce_grade import announce_grade
# from .scripts.crawl_classroom import crawl_classroom
# from .scripts.event_times import event_times
# from .scripts.grant_read_access import grant_read_access
# from .scripts.patch_project import patch_project


import typer

from .scripts.add_students import add_students
from .scripts.grant_read_access import grant_read_access
from .scripts.event_times import event_times
from .scripts.dev import dev

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
app = typer.Typer(context_settings=CONTEXT_SETTINGS)

app.command("add-student")(add_students)
app.command("grant-read-access")(grant_read_access)
app.command("event-times")(event_times)
# app.command("dev")(dev)

# @click.group(
#     invoke_without_command=True, context_settings=dict(help_option_names=["-h", "--help"])
# )
# @click.pass_context
# def cli(ctx):
#     """Toolkits for github courses"""
#     if ctx.invoked_subcommand is None:
#         click.echo(ctx.get_help())


# cli.add_command(event_times)
# cli.add_command(patch_project)
# cli.add_command(announce_grade)
# cli.add_command(crawl_classroom)
