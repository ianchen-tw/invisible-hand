from typing import Optional

import typer

from invisible_hand.config import app_context
from invisible_hand.errors import ERR_CANNOT_FETCH_TEAM


def dev(
    org: Optional[str] = typer.Option(None, help="Last name of person to greet."),
    age: str = typer.Option("", help="Some help message"),
):
    raise ERR_CANNOT_FETCH_TEAM(org="1", team_slug="bb")
    print(f"[dev]actual org :{org}")
    print(f"[dev]aa org :{app_context.config.github.organization}")

    print("nice")
