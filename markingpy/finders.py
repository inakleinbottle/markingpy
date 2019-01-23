"""
Submission finder tools.
"""

from abc import ABC, abstractmethod
import sqlite3
from pathlib import Path

from .import submission

__all__ = ["BaseFinder", "DirectoryFinder", "SQLiteFinder", "NullFinder"]


class BaseFinder(ABC):

    @abstractmethod
    def get_submissions(self, **kwargs):
        """Load submissions using this finder. Return a generator."""


class DirectoryFinder(BaseFinder):
    """
    Load submissions from a directory.
    """

    def __init__(self, path):
        path = self.path = Path(path)
        if path.exists() and not path.is_dir():
            print(path)
            raise NotADirectoryError("Expected a directory")

    def get_file_list(self):
        try:
            return [
                    file
                    for file in self.path.iterdir()
                    if file.is_file()
                    if file.name.endswith(".py")
                    ]
        except AttributeError:
            return None

    def get_submissions(self):
        file_list = self.get_file_list()
        if file_list is None:
            raise RuntimeError('No submissions found')
        for file in file_list:
            ref = file.name[:-3]
            source = file.read_text()
            yield submission.Submission(ref, source)


class SQLiteFinder(BaseFinder):

    def __init__(self, path, table, ref_field, source_field):
        self.path = Path(path)
        self.table = table
        self.ref_field = ref_field
        self.source_field = source_field

    def get_submissions(self, **kwargs):
        if not self.path.exists():
            raise RuntimeError(f"Path {self.path} does not exist")

        conn = sqlite3.connect(self.path)
        for ref, source in conn.execute(
            f"SELECT {self.ref_field}, {self.source_field}"
            f" FROM {self.table}"
        ):
            yield submission.Submission(ref, source)


class NullFinder(BaseFinder):

    def __init__(self, *subs):
        self.subs = subs

    def get_submissions(self, **kwargs):
        yield from self.subs
