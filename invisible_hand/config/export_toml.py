from typing import Dict, Optional

from tomlkit import comment, document, dumps, nl, table

from .base_config import Config


class _ERR_NON_VAILD_DEFAULT_CFG(Exception):
    """ Internal use,
    make sure that our default config is always valid
    """

    def __init__(self):
        super().__init__(self)


def add_commented_section(
    docu: document, section_name: str, dic: Dict, section_comment: Optional[str] = None,
):
    """ Add a section with comment
    """

    def build_table(header=None):
        try:
            t = table()
            if header:
                t.add(comment(header))

            for k, v in dic.items():
                if isinstance(v, Dict):
                    if v.get("comment"):
                        t.add(comment(v["comment"]))
                    elif v.get("comments"):
                        for c in v["comments"]:
                            t.add(comment(c))
                    else:
                        raise _ERR_NON_VAILD_DEFAULT_CFG
                    t.add(k, v["value"])
                    t.add(nl())
                else:
                    t.add(k, v)
        except:
            raise _ERR_NON_VAILD_DEFAULT_CFG
        return t

    docu.add(section_name, build_table(header=section_comment))


def export_default_config() -> str:
    """ Generate the default config file
    """

    def add_big_title(docu, title: str, width: int = 50):
        def side(width):
            return "|" + " " * (width - 2) + "|"

        lines = [
            "=" * width,
            side(width),
            f"|{title.center(width-2)}|",
            side(width),
            "=" * width,
        ]
        for _ in range(3):
            docu.add(nl())
        for line in lines:
            docu.add(comment(line))

    default_cfg = Config.get_default()
    docu = document()
    docu.add(comment("Config file for invisible-hand"))
    docu.add(comment("each section define the corresponding default config for scripts"))
    add_big_title(docu, "Env Configuration")

    add_commented_section(
        docu=docu,
        section_name="github",
        dic={
            "organization": {
                "comment": "Your GitHub organization (https://github.com/Organization/Repository/...)",
                "value": default_cfg.github.organization,
            },
            "personal_access_token": {
                "comments": [
                    "Your GitHub API token here, inside the quotation marks",
                    "https://github.com/blog/1509-personal-api-tokens",
                ],
                "value": default_cfg.github.personal_access_token,
            },
        },
    )

    add_commented_section(
        docu=docu,
        section_name="google_spreadsheet",
        section_comment="You need to config this section before using `hand annouce-grade`",
        dic={"spreadsheet_url": default_cfg.google_spreadsheet.spreadsheet_url,},
    )

    add_big_title(docu, "Scripts Configuration")

    add_commented_section(
        docu=docu,
        section_name="add_students",
        dic={"default_team_slug": default_cfg.add_students.default_team_slug},
    )

    add_commented_section(
        docu=docu,
        section_name="grant_read_access",
        dic={"reader_team_slug": default_cfg.grant_read_access.reader_team_slug,},
    )

    add_commented_section(
        docu=docu,
        section_name="crawl_classroom",
        dic={
            "login": {
                "comment": "Your login id in Github Classroom",
                "value": default_cfg.crawl_classroom.login,
            },
            "classroom_id": {
                "comment": "id field of your classroom RESTful page URL.",
                "value": default_cfg.crawl_classroom.classroom_id,
            },
        },
    )

    add_commented_section(
        docu=docu,
        section_name="event_times",
        dic={
            "deadline": {
                "comments": [
                    "Deadline for homework, in ISO8601 compatible format",
                    "For example `2019-11-12 23:59:59` (the timezone is set to your local timezone as default)",
                    "Or simply `2019-11-12`",
                ],
                "value": default_cfg.event_times.deadline,
            }
        },
    )

    add_commented_section(
        docu=docu,
        section_name="announce_grade",
        dic={
            "feedback_source_repo": {
                "comment": "You're not supposed to change this variable",
                "value": default_cfg.announce_grade.feedback_source_repo,
            }
        },
    )

    return dumps(docu)
