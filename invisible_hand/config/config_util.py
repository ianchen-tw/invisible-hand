import importlib.resources as pkg_resources
from pathlib import Path
from shutil import copyfile

from . import templates

def init_config_file(file_name: str, output_name: str):
    '''Copy the file inside ./template to working dir, will fail if file already exists'''
    with pkg_resources.path(templates, file_name) as tmpl_path:
        if Path(output_name).exists():
            print(f'config file `{output_name}` already exists.')
            return
        copyfile(src=tmpl_path, dst=output_name)
        print(f'Create config file: {output_name}')
