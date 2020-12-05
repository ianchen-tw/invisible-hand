from typing import Dict, Optional

from tomlkit import comment, document, dumps, nl, table


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

    def build_table():
        try:
            t = table()

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

    if section_comment:
        docu.add(comment(section_comment))

    docu.add(section_name, build_table())


def create_default_config() -> str:
    """ Generate the default config file
    """
    docu = document()
    docu.add(comment("Config file for invisible-hand"))
    docu.add(comment("each section define the corresponding default config for scripts"))

    add_commented_section(
        docu=docu,
        section_name="github",
        dic={
            "personal_access_token": {
                "comments": [
                    "Your GitHub API token here, inside the quotation marks",
                    "https://github.com/blog/1509-personal-api-tokens",
                ],
                "value": "your-github-personal-access-token",
            },
        },
    )

    add_commented_section(
        docu=docu,
        section_name="google_spreadsheet",
        dic={
            "spreadsheet_url": "your-spreadsheet-id",
            "cred_filename": "client_secret.json",
        },
    )

    add_commented_section(
        docu=docu,
        section_name="crawl_classroom",
        dic={"login": "your-github-id", "classroom_id": "classroom-id-in-url"},
    )
    add_commented_section(
        docu=docu,
        section_name="grant_read_access",
        dic={"reader_team_slug": "2020-teaching-team",},
    )

    add_commented_section(
        docu=docu, section_name="add_students", dic={"default_team_slug": "2020-students"}
    )

    add_commented_section(
        docu=docu, section_name="event_times", dic={"deadline": "2019-11-12 23:59:59"}
    )
    add_commented_section(
        docu=docu,
        section_name="announce_grade",
        dic={
            "feedback_source_repo": {
                "comment": "You're not supposed to change this variable",
                "value": "Hw-manager",
            }
        },
    )

    return dumps(docu)
