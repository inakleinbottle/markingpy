
from abc import ABC, abstractmethod

from . import submission


class BaseFinder(ABC):

    @abstractmethod
    def get_submissions(self, **kwargs):
        """Load submissions using this finder. Return a generator."""


class DirectoryFinder(BaseFinder):
    """
    Load submissions from a directory.
    """

    def __init__(self, path):
        self.path = path
        if not path.is_directory():
            raise NotADirectoryError('Expected a directory')
        self.file_list = [file for file in path.iterdir()
                          if file.is_file()
                          if file.name.endswith('.py')]

    def get_submissions(self):
        for file in self.file_list:
            yield submission.Submission(file)
