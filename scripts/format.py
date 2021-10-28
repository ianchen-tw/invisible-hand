# format project code

import argparse
import subprocess as sp
from pathlib import Path
from sys import exit as sys_exit
from typing import Union

from rich.console import Console

console = Console()


def main():
    modes = ["format", "lint", "all"]
    parser = argparse.ArgumentParser(description="tool")
    parser.add_argument("mode", metavar="Mode", help="|".join(modes))
    parser.add_argument(
        "path", metavar="Path", nargs="?", default=".", help="path to run script"
    )

    def get_arg(attr: str):
        return getattr(parser.parse_args(), attr)

    mode = get_arg("mode")
    # path = Path(get_arg("path")).resolve()
    path = Path(get_arg("path"))

    if mode not in modes:
        console.log(f"Non valid mode arg: [red]{mode}[/]")

    try:
        if mode in ["all", "format"]:
            format_project(path)
        if mode in ["all", "lint"]:
            lint_project(path)
        log("Prettier finished")
        sys_exit(0)
    except sp.CalledProcessError:
        console.log("[red]Task failed[/]")
        console.log("Please check your code before going any futher")
        sys_exit(1)


def log(msg: str):
    console.log(f"[yellow]{msg}[/]")


def lint_project(folder: Union[str, Path]):
    folder = str(folder)
    log(f"Lint code: {folder}")
    sp.run(["pyflakes", str(folder)]).check_returncode()
    # sp.run(["mypy", str(folder)]).check_returncode()


def format_project(folder: Union[str, Path]):
    folder = str(folder)
    log(f"Format code: {folder}")
    sp.run(["black", folder]).check_returncode()

    log("Remove unused imports")

    sp.run(
        [
            "autoflake",
            "--remove-all-unused-imports",
            "--recursive",
            "--remove-unused-variables",
            "--in-place",
            folder,
            "--exclude=__init__.py",
        ]
    ).check_returncode()

    log("Sort & Gather imports")
    sp.run(["isort", folder]).check_returncode()


if __name__ == "__main__":
    main()
