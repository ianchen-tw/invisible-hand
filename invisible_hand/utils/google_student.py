from typing import Dict, List, Optional

from xlsxwriter.utility import xl_col_to_name
import pygsheets

from ..config.gsheet import config_gsheet

def get_all_record(wks: pygsheets.Worksheet, head=1):
    endtag = f'{xl_col_to_name(wks.cols-1)}{wks.rows}'
    grange = pygsheets.GridRange(end=endtag)
    data = wks.get_values(
        grange=grange,
        include_tailing_empty=True,
        include_tailing_empty_rows=False
    )
    idx = head-1
    keys = data[idx]
    field_index_map = {field: n for n,
                       field in enumerate(keys) if field.strip() != ""}
    vals = []
    for row in data[idx+1:]:
        val = {field: row[i] for field, i in field_index_map.items()}
        vals.append(val)
    return vals

class Gstudents:
    def __init__(self, url=config_gsheet['spreadsheet_url']):
        self.gc = pygsheets.authorize()
        self.sht = self.gc.open_by_url(url)
        self.infos = self.sht.worksheet('title', 'StudentInfo')
        self.config = {
            'main_wks_title': 'StudentInfo',
            'main_wks_required_fields':
                [
                    'github_handle',
                    'student_id',
                    'name',
                    'email',
                ],
            'main_kws_key_field': 'student_id'
        }

    def get_students(self) -> List[Dict[str, str]]:
        return get_all_record(self.sht.worksheet_by_title(self.config['main_wks_title']))

    def get_student(self, student_id ) -> Optional[Dict]:
        '''Fetch a single students info, will traverse the entire table
            Use get_students manually if you need to get each student's info
        '''
        students = self.get_students()
        for s in students:
            if student_id == s['student_id']:
                return s
        return None

    def left_join(self, right_sheet_title) -> List[Dict[str, str]]:
        left_dicts = self.get_students()
        right_dicts = get_all_record(
            self.sht.worksheet_by_title(right_sheet_title))

        def left_matching(left, right, key_field: str):
            for l in left:
                for r in right:
                    if l[key_field] == r[key_field]:
                        yield l, r
        joined_infos = []
        for left, right in left_matching(left_dicts, right_dicts, self.config['main_kws_key_field']):
            student = {**left, **right}
            joined_infos.append(student)
        return joined_infos

if __name__ == "__main__":
    url = "https://docs.google.com/spreadsheets/d/1WlbKDBdhC03m_mFikWwwveDvSQKwKKo20SO9KlbeSqQ/edit?ouid=109372349474156491416&usp=sheets_home"
    student = Gstudents(url)
    for i in student.left_join("hw1"):
        print(i)
        print("-"*20)
