import sys
import os
import shutil
import logging
from typing import List
from pathlib import Path


class FileManager:

    @staticmethod
    def get_executable_relative_path(file_path: str) -> str:
        path: str = file_path
        if getattr(sys, 'frozen', False):
            path = (Path(sys.executable).parent / file_path).__str__()
        return path

    @staticmethod
    def get_storage_path(file_path: str) -> str:
        return os.path.join(os.getenv('APPDATA'), 'Valorant-Zone-Stats', file_path)

    @staticmethod
    def migrate_files(file_paths: List[str]) -> int:
        files_migrated: int = 0
        for path in file_paths:
            from_path: str = FileManager.get_executable_relative_path(path)
            if os.path.isfile(from_path):
                shutil.move(from_path, FileManager.get_storage_path(path))
                files_migrated += 1
        return files_migrated


if not os.path.isdir(FileManager.get_storage_path('')):
    os.mkdir(FileManager.get_storage_path(''))

logger: logging.Logger = logging.getLogger('Valorant-Zone-Stats')
logger.setLevel(logging.DEBUG)
# create file handler
fh = logging.FileHandler(FileManager.get_storage_path('debug.log'), mode='w')
fh.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter(fmt='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                              datefmt='%H:%M:%S')
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(logging.StreamHandler(sys.stdout))

logger.debug('Initialized logger')

