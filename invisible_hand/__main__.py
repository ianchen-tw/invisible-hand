from .utils.google_student import Gstudents
from .cli import cli

# def test():
    # g = Gsheet(spreadsheetId='1WlbKDBdhC03m_mFikWwwveDvSQKwKKo20SO9KlbeSqQ')
    # g.playground()

    # g = Gstudents()

    # print( g.gsheet.sheets().get(sid) )
    # print(gsheet.get_values())
    # print(gsheet.get_values(A1=SAMPLE_RANGE_NAME))
    # print(f'title list: {gsheet.get_title_list()}')

if __name__ == "__main__":
    cli()
