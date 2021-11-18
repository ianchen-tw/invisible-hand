from pydantic import BaseModel
from dynaconf import Dynaconf


class HandConfig(BaseModel):
    """ Program config class"""

    class Config:
        """used to config pydantic's behavior"""

        orm_mode = True

    class Github(BaseModel):
        token: str
        org: str

    class Google(BaseModel):
        url: str
        cred_filename: str

    class CrawlClassroom(BaseModel):
        gh_login: str
        classroom_id: str

    class GrantReadAccess(BaseModel):
        reader_team: str

    class AddStudens(BaseModel):
        student_team: str

    class EventTimes(BaseModel):
        compare_deadline: str

    class AnnounceGrade(BaseModel):
        feedback_src_repo: str

    github: Github
    google_spreadsheet: Google
    crawl: CrawlClassroom
    grant: GrantReadAccess
    add: AddStudens
    times: EventTimes
    announce: AnnounceGrade


_dyna_settings = Dynaconf(settings_files=["config/settings.toml"])
settings: HandConfig = HandConfig.from_orm(_dyna_settings)

