#      Markingpy automatic grading tool for Python code.
#      Copyright (C) 2019 University of East Anglia
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""
Submission finder tools.
"""

from abc import ABC, abstractmethod
import sqlite3
from pathlib import Path
from typing import Union, List, Generator, Optional, Any

from .import submission

__all__ = ["BaseFinder", "DirectoryFinder", "SQLiteFinder", "NullFinder"]
SUB_GENERATOR = Generator[submission.Submission, None, None]


class BaseFinder(ABC):

    @abstractmethod
    def get_submissions(self, **kwargs):
        """Load submissions using this finder. Return a generator."""


class DirectoryFinder(BaseFinder):
    """
    Load submissions from a directory.
    """

    def __init__(self, path: Union[str, Path]):
        path = self.path = Path(path)
        if path.exists() and not path.is_dir():
            print(path)
            raise NotADirectoryError("Expected a directory")

    def get_file_list(self) -> Optional[List[Path]]:
        try:
            return [
                file
                for file in self.path.iterdir()
                if file.is_file()
                if file.name.endswith(".py")
            ]

        except AttributeError:
            return None

    def get_submissions(self) -> SUB_GENERATOR:
        file_list = self.get_file_list()
        if file_list is None:
            raise RuntimeError('No submissions found')

        for file in file_list:
            ref = file.name[:-3]
            source = file.read_text()
            yield submission.Submission(ref, source)


class SQLiteFinder(BaseFinder):

    def __init__(
        self,
        path: Union[str, Path],
        table: str,
        ref_field: str,
        source_field: str,
    ):
        self.path = Path(path)
        self.table = table
        self.ref_field = ref_field
        self.source_field = source_field

    def get_submissions(self, **kwargs: Any) -> SUB_GENERATOR:
        if not self.path.exists():
            raise RuntimeError(f"Path {self.path} does not exist")

        conn = sqlite3.connect(self.path)
        for ref, source in conn.execute(
            f"SELECT {self.ref_field}, {self.source_field}"
            f" FROM {self.table}"
        ):
            yield submission.Submission(ref, source)


class NullFinder(BaseFinder):

    def __init__(self, *subs: submission.Submission):
        self.subs = subs

    def get_submissions(self, **kwargs: Any) -> SUB_GENERATOR:
        yield from self.subs
