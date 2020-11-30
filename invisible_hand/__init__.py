from colorama import init as colorama_init

from rich.console import Console

from .core.console_color import custom_theme
from .config.github import init_constants as github_init_constants
from .config.gsheet import init_constants as gsheet_init_constants

colorama_init(autoreset=True)

github_init_constants()
gsheet_init_constants()

console = Console(theme=custom_theme)


def console_txt(txt: str):
    """ Highlighted text for console
    """
    with console.capture() as capture:
        console.print(txt)
    return capture.get()
