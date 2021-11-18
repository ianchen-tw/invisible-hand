from typer import Argument


def check_env(
    cmd: str = Argument(metavar="cmd", default=..., help="command name to check",)
):
    """Check the environemnt is okay"""
