from abc import ABC, abstractmethod
import sqlite3
from pathlib import Path

from . import submission


__all__ = ["DirectoryFinder", "SQLiteFinder"]


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
        if not path.is_dir():
            raise NotADirectoryError("Expected a directory")
        self.file_list = [
            file
            for file in path.iterdir()
            if file.is_file()
            if file.name.endswith(".py")
        ]

    def get_submissions(self):
        for file in self.file_list:
            ref = file.name[:-3]
            source = file.read()
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
    def get_submissions(self, **kwargs):
        yield from []
