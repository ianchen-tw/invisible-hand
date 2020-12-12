from pydantic import BaseModel


class Config(BaseModel):
    """
        The Config class
    """

    class Github(BaseModel):
        personal_access_token: str
        organization: str

    class Google(BaseModel):
        spreadsheet_url: str

    class CrawlClassroom(BaseModel):
        login: str
        classroom_id: str

    class GrantReadAccess(BaseModel):
        reader_team_slug: str

    class AddStudens(BaseModel):
        default_team_slug: str

    class EventTimes(BaseModel):
        deadline: str

    class AnnounceGrade(BaseModel):
        feedback_source_repo: str

    github: Github
    google_spreadsheet: Google
    crawl_classroom: CrawlClassroom
    grant_read_access: GrantReadAccess
    add_students: AddStudens
    event_times: EventTimes
    announce_grade: AnnounceGrade

    @staticmethod
    def get_default():
        return Config(
            github=Config.Github(
                personal_access_token="your-github-personal-access-token",
                organization="compiler-s20",
            ),
            google_spreadsheet=Config.Google(spreadsheet_url="your-spreadsheet-id"),
            crawl_classroom=Config.CrawlClassroom(
                login="your-github-id", classroom_id="classroom-id-in-url"
            ),
            grant_read_access=Config.GrantReadAccess(
                reader_team_slug="2020-teaching-team"
            ),
            add_students=Config.AddStudens(default_team_slug="2020-students"),
            event_times=Config.EventTimes(deadline="2019-11-12 23:59:59"),
            announce_grade=Config.AnnounceGrade(feedback_source_repo="Hw-manager"),
        )
