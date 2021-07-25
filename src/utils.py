import sys
from pathlib import Path


def get_executable_relative_path(file):
    path: str
    if getattr(sys, 'frozen', False):
        path = (Path(sys.executable).parent / file).__str__()
    else:
        path = file
    return path
