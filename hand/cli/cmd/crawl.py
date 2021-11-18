from typer import Argument


def crawl_classroom(
    hw_title: str = Argument(..., help="homework submission to crawl"),
    output: str = Argument(..., help="filename to output your result"),
):
    """Get student's submissions from Github Classroom
    """
    print("check classroom id")
    print("check gh_login")
    print("check output file does not exists")
