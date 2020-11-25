from colorama import init as colorama_init
from rich.console import Console

from .config.github import init_constants as github_init_constants
from .config.gsheet import init_constants as gsheet_init_constants

colorama_init(autoreset=True)

github_init_constants()
gsheet_init_constants()

console = Console()
