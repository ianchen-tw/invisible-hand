# import click

from pathlib import Path
from configparser import ConfigParser

from .config_util import init_config_file

# These variables will be set in init_constants()
config_github = None
config_add_students = None
config_event_times = None
config_announce_grade = None
config_crawl_classroom = None
config_grant_read_access = None

# will be call inside invisible_hand/__init__.py


def init_constants():
    '''initialize all constants'''
    global config_github
    global config_announce_grade
    global config_add_students
    global config_event_times
    global config_crawl_classroom
    global config_grant_read_access

    template_name = 'github.ini'
    cfile = "github_config.ini"

    if not Path(cfile).exists():
        init_config_file(template_name, cfile)
        # print('propagate config files')
        # sys.exit(1)
    config = ConfigParser()
    config.read(cfile)

    # export global variables
    config_github = dict(config['github'])
    config_event_times = dict(config['event_times'])
    config_add_students = dict(config['add_students'])
    config_announce_grade = dict(config['announce_grade'])
    config_crawl_classroom = dict(config['crawl_classroom'])
    config_grant_read_access = dict(config['grant_read_access'])
