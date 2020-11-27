import typer

from invisible_hand import console
from invisible_hand.errors import ERR_GIT_CREDENTIAL_HELPER_NOT_FOUND


def dev(
    name: str = typer.Option("", help="Last name of person to greet."),
    age: str = typer.Option("", help="Some help message"),
):
    console.log("good")
    a = 87787
    raise ERR_GIT_CREDENTIAL_HELPER_NOT_FOUND()
    # print(f"hello: {name}")
