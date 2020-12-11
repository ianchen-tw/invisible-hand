import string
from typing import Dict, List, Optional

import pygsheets
from pydantic import BaseModel
from xlsxwriter.utility import xl_col_to_name

from invisible_hand.config import app_context
from invisible_hand.ensures import ensure_client_secret_json_exists, ensure_config_exists
from ..errors import ERR_REQUIRE_NO_SPACE, ERR_UNIQUE_STUDENT_ID


class StudentInfo(BaseModel):
    # student_id must be unique
    student_id: str

    github_handle: str
    name: Optional[str] = None
    email: Optional[str] = None


def contains_space(word: str) -> bool:
    """test if there's any white space in the give word"""
    for s in word:
        if s.isspace():
            return True
    return False


class pygsheetInteractor:
    def __init__(self, pyg=pygsheets):
        ensure_client_secret_json_exists()
        self.gc = pyg.authorize(
            client_secret=app_context.config_manager.google_client_secret_path
        )
        self.sht = None

    def open_by_url(self, url):
        self.sht = self.gc.open_by_url(url)

    def _get_wks_by_title(self, title):
        if self.sht is None:
            raise RuntimeError("Call open_by_url before using any function")
        return self.sht.worksheet_by_title(title)

    def get_all_record(self, title, head=1) -> List[Dict]:
        wks = self._get_wks_by_title(title)
        endtag = f"{xl_col_to_name(wks.cols-1)}{wks.rows}"

        grange = pygsheets.GridRange(end=endtag)

        data = wks.get_values(
            grange=grange, include_tailing_empty=True, include_tailing_empty_rows=False
        )

        idx = head - 1
        keys = data[idx]
        field_index_map = {
            field: n for n, field in enumerate(keys) if field.strip() != ""
        }
        vals = []
        for row in data[idx + 1 :]:
            val = {field: row[i] for field, i in field_index_map.items()}
            vals.append(val)
        return vals


class Gstudents:
    def __init__(self, url: Optional[str] = None, actor=None):
        if url:
            self.url = url
        else:
            ensure_config_exists()
            self.url = app_context.config.google_spreadsheet.spreadsheet_url

        self.actor = actor if actor is not None else pygsheetInteractor()
        self.actor.open_by_url(self.url)

        self.config = {
            "main_wks_title": "StudentInfo",
            "main_wks_required_fields": ["github_handle", "student_id", "name", "email",],
            "main_kws_key_field": "student_id",
        }

        # parse and get student infos
        student_infos = self._build_student_info_records()
        self._ensure_no_space_in_student_fields(student_infos)
        self._ensure_unique_student_id(student_infos)
        self.student_infos: List[StudentInfo] = student_infos

    def _build_student_info_records(self) -> List[StudentInfo]:
        """Get student info from google sheet and do preliminary test"""
        records = self.actor.get_all_record(self.config["main_wks_title"])
        student_infos = []

        def is_valid(word: str) -> bool:
            """if the given word contains any printable character.
            """
            word = word.translate({ord(c): None for c in string.whitespace})
            return len(word) > 0

        for record in records:
            sid = record.get("student_id")
            handle = record.get("github_handle")
            name = record.get("name")
            email = record.get("email")
            if is_valid(sid) and is_valid(handle):
                student_infos.append(
                    StudentInfo(
                        student_id=sid, github_handle=handle, name=name, email=email,
                    )
                )
            elif is_valid(sid) or is_valid(handle):
                fields: Dict[str, str] = self.config["main_wks_required_fields"]
                uncomplete_record = {f: record.get(f) for f in fields}
                # @todo: show warning using log
                print(f"skip: uncomplete field - {uncomplete_record}")
        return student_infos

    def get_student_infos(self) -> List[StudentInfo]:
        return self.student_infos

    def get_students(self) -> List[Dict[str, str]]:
        """Return the student infos in dict"""
        result = []
        for s in self.student_infos:
            result.append(dict(s))
        return result

    def get_student_info(self, student_id: str) -> Optional[StudentInfo]:
        """Fetch a single students info, will traverse the entire table
        Use get_students manually if you need to get each student's info
        """
        students: List[StudentInfo] = self.student_infos
        for s in students:
            if student_id == s.student_id:
                return s
        return None

    def get_student(self, student_id: str) -> Optional[Dict[str, str]]:
        student = self.get_student_info(student_id)
        if student:
            return dict(student)
        return None

    def left_join(self, right_sheet_title) -> List[Dict[str, str]]:
        right_dicts = self.actor.get_all_record(right_sheet_title)

        def left_matching(left, right, key_field: str):
            for info in left:
                for r in right:
                    l_val = getattr(info, key_field)
                    r_val = r.get(key_field)
                    if l_val and r_val and l_val == r_val:
                        yield dict(info), r

        joined_infos = []
        for left, right in left_matching(
            self.student_infos, right_dicts, self.config["main_kws_key_field"]
        ):
            student = {**left, **right}
            joined_infos.append(student)
        return joined_infos

    def _ensure_unique_student_id(self, student_infos: List[StudentInfo]):
        ids = set()
        errors: List[Dict] = []
        for info in student_infos:
            if info.student_id not in ids:
                ids.add(info.student_id)
            else:
                errors.append(dict(info))
        if len(errors) > 0:
            raise ERR_UNIQUE_STUDENT_ID(
                explanation="Student ID should be unique, found:", instances=errors
            )

    def _ensure_no_space_in_student_fields(self, student_infos: List[StudentInfo]):
        errors: List[str] = []
        for info in student_infos:
            for field in self.config["main_wks_required_fields"]:
                value = getattr(info, field)
                if contains_space(value):
                    errors.append(value)
        if len(errors) > 0:
            raise ERR_REQUIRE_NO_SPACE(
                "Detect white spaces in fields, please remove it before going any further",
                errors,
            )
