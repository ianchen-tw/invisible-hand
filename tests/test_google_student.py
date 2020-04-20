import pytest
import unittest
from unittest.mock import patch

from invisible_hand.utils.google_student import Gstudents
from invisible_hand.utils.google_student import pygsheetInteractor

import pygsheets

# TODO:
# test if pygsheet work as supposed

class TestInteractor:
    ''' Test Interactor work properly if pygsheet does
    '''
    def test_interactor_need_to_call_open_url_before_use(self):
        actor = pygsheetInteractor(pygsheets)
        with pytest.raises(RuntimeError):
            actor.get_all_record('not-important')

    @patch('pygsheets.authorize')
    def test_interactor_auth_on_create(self,pyg_auth):
        actor = pygsheetInteractor()
        pyg_auth.assert_called_once()

    @patch('pygsheets.authorize')
    def test_get_all_record(self, pyg_auth):
        '''return [{'col_name','val'}...]
        '''
        actor = pygsheetInteractor()
        actor.open_by_url('test_sheet')

        mock_matrix = [
            ['c1','c2'],
            ['a2', 'a3'],
            ['b4', 'b3']
        ]
        ans = [
            {'c1': 'a2', 'c2': 'a3'},
            {'c1': 'b4', 'c2': 'b3'}
        ]

        pyg_wks = pyg_auth().open_by_url().worksheet_by_title()
        pyg_wks.get_values.return_value = mock_matrix.copy()
        pyg_wks.cols, pyg_wks.rows=2, 2
        ret = actor.get_all_record('test_wks_title')
        assert(ret == ans)


class mockInteractor(pygsheetInteractor):
    records = [
        {'student_id': 'A12345', 'name':'jonny'},
        {'student_id': 'B99203', 'name':'Ian'}]
    right_records = [
        {'student_id': 'A12345', 'age':'18'},
        {'student_id': 'B99203', 'age':'23'}]

    def _test_set_records(self, records):
        '''Additional func for mockInteractor'''
        self.records = records.copy()

    def __init__(self):
        pass

    def open_by_url(self, *args, **kwargs):
        self.open_by_url_called = True

    def get_all_record(self, title, head=1):
        if title == "right_records":
            return self.right_records
        return self.records

@pytest.fixture(scope='module')
def setupGstudent():
    return Gstudents('test_url', mockInteractor())

class TestGstudents:
    '''Test Gstudents work properly with Interactor
    '''

    def test_init_must_call_open_by_url(self):
        actor = mockInteractor()
        gstudents = Gstudents('test_url', actor)
        assert(actor.open_by_url_called == True)

    def test_gstudent_get_students(self, setupGstudent):
        gstudent = setupGstudent
        assert( mockInteractor.records == gstudent.get_students())

    def test_left_join(self, setupGstudent):
        gstudent = setupGstudent
        ret = gstudent.left_join('right_records')
        ans = [
            {'student_id': 'A12345', 'name':'jonny', 'age':'18'},
            {'student_id': 'B99203', 'name':'Ian', 'age': '23'}
        ]
        assert(ans == ret)

    def test_find_student(self, setupGstudent):
        actor = mockInteractor()
        gstudent = Gstudents('test_url', actor)
        actor._test_set_records([
            {'student_id': 'B1', 'name':'john'},
            {'student_id': 'B2', 'name':'Ann'}]
        )
        stu = gstudent.get_student('B1')
        assert( {'student_id': 'B1', 'name':'john'} == stu )

    def test_raise_runtime_err_when_finding_multiple_student_with_same_id(self):
        actor = mockInteractor()
        gstudent = Gstudents('test_url', actor)
        actor._test_set_records([
            {'student_id': 'B1', 'name':'john'},
            {'student_id': 'B1', 'name':'Ann'}]
        )
        with pytest.raises(RuntimeError, match=r"duplicate student_id :.*") as excinfo:
            gstudent.get_student('B1')
