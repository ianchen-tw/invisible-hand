# Initialize google spreadsheet constants
from configparser import ConfigParser
from pathlib import Path

from .config_util import init_config_file

config_gsheet = None


def init_constants():
    """initialize all constants"""
    global config_gsheet
    template_name = "google_sheet.ini"
    cfile = "gsheet_config.ini"

    if not Path(cfile).exists():
        init_config_file(template_name, cfile)

    config = ConfigParser()
    config.read(cfile)

    # export global variables
    config_gsheet = dict(config["google_spreadsheet"])
