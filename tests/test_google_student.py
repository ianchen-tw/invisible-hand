import pytest
from unittest.mock import patch

from hand.utils.google_student import Gstudents
from hand.utils.google_student import pygsheetInteractor

import pygsheets

from hand.errors import ERR_UNIQUE_STUDENT_ID, ERR_REQUIRE_NO_SPACE

# TODO:
# test if pygsheet work as supposed


class TestInteractor:
    """Test Interactor work properly if pygsheet does"""

    def test_interactor_need_to_call_open_url_before_use(self):
        actor = pygsheetInteractor(pygsheets)
        with pytest.raises(RuntimeError):
            actor.get_all_record("not-important")

    @patch("pygsheets.authorize")
    def test_interactor_auth_on_create(self, pyg_auth):
        pygsheetInteractor()
        pyg_auth.assert_called_once()

    @patch("pygsheets.authorize")
    def test_get_all_record(self, pyg_auth):
        """return [{'col_name','val'}...]"""
        actor = pygsheetInteractor()
        actor.open_by_url("test_sheet")

        mock_matrix = [["c1", "c2"], ["a2", "a3"], ["b4", "b3"]]
        ans = [{"c1": "a2", "c2": "a3"}, {"c1": "b4", "c2": "b3"}]

        pyg_wks = pyg_auth().open_by_url().worksheet_by_title()
        pyg_wks.get_values.return_value = mock_matrix.copy()
        pyg_wks.cols, pyg_wks.rows = 2, 2
        ret = actor.get_all_record("not-important")
        assert ret == ans


class mockInteractor(pygsheetInteractor):
    student_info_table = [
        {
            "student_id": "A1",
            "github_handle": "aaa",
            "name": "Andy",
            "email": "good@example.com",
        },
        {
            "student_id": "A2",
            "github_handle": "bbb",
            "name": "Ben",
            "email": "good@example.com",
        },
        {
            "student_id": "A3",
            "github_handle": "ccc",
            "name": "Cindy",
            "email": "good@example.com",
        },
    ]
    default_records = [
        {"student_id": "A1", "score": "99"},
        {"student_id": "A2", "score": "102"},
    ]

    def _test_set_records(self, records, title=None):
        """Additional func for mockInteractor"""
        if title == "StudentInfo":
            self.student_info_table = records.copy()
        else:
            self.default_records = records.copy()

    def __init__(self):
        pass

    def open_by_url(self, *args, **kwargs):
        self.open_by_url_called = True

    def get_all_record(self, title, head=1):
        if title == "StudentInfo":
            return self.student_info_table
        return self.default_records


@pytest.fixture(scope="function")
def gstudent():
    return Gstudents("test_url", mockInteractor())


class TestGstudents:
    """Test Gstudents work properly with Interactor"""

    def test_init_must_call_open_by_url(self, gstudent):
        assert gstudent.actor.open_by_url_called == True

    def test_gstudent_get_students(self, gstudent):
        assert mockInteractor.student_info_table == gstudent.get_students()

    def test_left_join(self, gstudent):
        ret = gstudent.left_join("hw1")
        ans = [
            {
                "student_id": "A1",
                "github_handle": "aaa",
                "name": "Andy",
                "email": "good@example.com",
                "score": "99",
            },
            {
                "student_id": "A2",
                "github_handle": "bbb",
                "name": "Ben",
                "email": "good@example.com",
                "score": "102",
            },
        ]
        assert ans == ret

    def test_find_student(self, gstudent):
        stu = gstudent.get_student("A1")
        assert {
            "student_id": "A1",
            "github_handle": "aaa",
            "name": "Andy",
            "email": "good@example.com",
        } == stu

    def test_error_on_duplicate_id(self):
        actor = mockInteractor()
        actor._test_set_records(
            [
                {
                    "student_id": "A1",
                    "github_handle": "aaa",
                    "name": "Andy",
                    "email": "good@example.com",
                },
                {
                    "student_id": "A1",
                    "github_handle": "bbb",
                    "name": "Ben",
                    "email": "good@example.com",
                },
                {
                    "student_id": "A3",
                    "github_handle": "ccc",
                    "name": "Cindy",
                    "email": "good@example.com",
                },
            ],
            title="StudentInfo",
        )
        with pytest.raises(ERR_UNIQUE_STUDENT_ID):
            Gstudents("test_url", actor)

    def test_error_on_spacy_config_fields(self):
        actor = mockInteractor()
        actor._test_set_records(
            [
                {
                    "student_id": " A1",
                    "github_handle": "aa a",
                    "name": "Andy",
                    "email": "good@example.com",
                },
            ],
            title="StudentInfo",
        )
        with pytest.raises(ERR_REQUIRE_NO_SPACE):
            Gstudents("test_url", actor)
