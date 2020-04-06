from .utils.google_student import Gstudents
import click

from prompt_toolkit import prompt

from .scripts.github_add_students import add_students
from .scripts.github_event_times import event_times
from .scripts.github_patch_project import patch_project
from .scripts.github_announce_grade import announce_grade
from .scripts.github_crawl_classroom import crawl_classroom
from .scripts.github_grant_read_access import grant_read_access


@click.group(invoke_without_command=True, context_settings=dict(help_option_names=["-h", "--help"]))
@click.pass_context
def cli(ctx):
    '''Toolkits for compiler-f19
    '''
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cli.add_command(add_students)
cli.add_command(event_times)
cli.add_command(patch_project)
cli.add_command(announce_grade)
cli.add_command(crawl_classroom)
cli.add_command(grant_read_access)


def test():

    # g = Gsheet(spreadsheetId='1WlbKDBdhC03m_mFikWwwveDvSQKwKKo20SO9KlbeSqQ')
    # g.playground()

    g = Gstudents()

    # print( g.gsheet.sheets().get(sid) )
    # print(gsheet.get_values())
    # print(gsheet.get_values(A1=SAMPLE_RANGE_NAME))
    # print(f'title list: {gsheet.get_title_list()}')


if __name__ == "__main__":
    # test()
    cli()
