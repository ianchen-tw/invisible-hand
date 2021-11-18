from attr import attrs

from ._protocol import Script


@attrs(auto_attribs=True)
class ScriptPublishGrade(Script):
    org: str
    dry: bool
    yes: bool

    def run(self):
        print("step: fetch grade from gsheet")
        print("step: create tmp-folder for generate final feedbacks")

        print("step: clone feedback source repo")
        print("step: rendering feedbacks")
        print("step: handle only-id")
        print("step: push to student repo")
