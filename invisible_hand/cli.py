import typer

from .scripts.add_students import add_students
from .scripts.grant_read_access import grant_read_access
from .scripts.event_times import event_times
from .scripts.patch_project import patch_project
from .scripts.announce_grade import announce_grade
from .scripts.crawl_classroom import crawl_classroom
from .scripts.dev import dev

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
app = typer.Typer(context_settings=CONTEXT_SETTINGS)

app.command("add-student")(add_students)
app.command("grant-read-access")(grant_read_access)
app.command("event-times")(event_times)
app.command("patch-project")(patch_project)
app.command("crawl-classroom")(crawl_classroom)
app.command("announce-grade")(announce_grade)
# app.command("dev")(dev)

