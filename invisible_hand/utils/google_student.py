from typing import Dict, List, Optional

import pygsheets
from xlsxwriter.utility import xl_col_to_name

from ..config.gsheet import config_gsheet


class pygsheetInteractor:
    def __init__(self, pyg=pygsheets):
        self.gc = pyg.authorize()
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
    def __init__(self, url=config_gsheet["spreadsheet_url"], actor=None):
        self.actor = actor if actor is not None else pygsheetInteractor()
        self.actor.open_by_url(url)

        self.config = {
            "main_wks_title": "StudentInfo",
            "main_wks_required_fields": [
                "github_handle",
                "student_id",
                "name",
                "email",
            ],
            "main_kws_key_field": "student_id",
        }

    def get_students(self) -> List[Dict[str, str]]:
        return self.actor.get_all_record(self.config["main_wks_title"])

    def get_student(self, student_id) -> Optional[Dict]:
        """Fetch a single students info, will traverse the entire table
        Use get_students manually if you need to get each student's info
        """
        students = self.get_students()
        ret = []
        for s in students:
            if student_id == s["student_id"]:
                ret.append(s)

        if len(ret) > 1:
            raise RuntimeError(f"duplicate student_id :{ret}")
        return ret[0] if len(ret) > 0 else None

    def left_join(self, right_sheet_title) -> List[Dict[str, str]]:
        # TODO: check id collision
        left_dicts = self.get_students()
        right_dicts = self.actor.get_all_record(right_sheet_title)

        def left_matching(left, right, key_field: str):
            for l in left:
                for r in right:
                    if l[key_field] == r[key_field]:
                        yield l, r

        joined_infos = []
        for left, right in left_matching(
            left_dicts, right_dicts, self.config["main_kws_key_field"]
        ):
            student = {**left, **right}
            joined_infos.append(student)
        return joined_infos
