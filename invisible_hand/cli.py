import click

from .scripts.add_students import add_students
from .scripts.announce_grade import announce_grade
from .scripts.crawl_classroom import crawl_classroom
from .scripts.event_times import event_times
from .scripts.grant_read_access import grant_read_access
from .scripts.patch_project import patch_project


@click.group(
    invoke_without_command=True, context_settings=dict(help_option_names=["-h", "--help"])
)
@click.pass_context
def cli(ctx):
    """Toolkits for github courses"""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cli.add_command(add_students)
cli.add_command(event_times)
cli.add_command(patch_project)
cli.add_command(announce_grade)
cli.add_command(crawl_classroom)
cli.add_command(grant_read_access)


def main():
    cli()
