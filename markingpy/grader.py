"""
Grading tool for python files.
"""


import logging
import os
import sys
import tempfile
import traceback

from pathlib import Path
from typing import (Type, )

from . import markscheme
from . import submission

logger = logging.getLogger(__name__)
__all__ = ['Grader']


class Grader:
    """
    Grader object drives the grading for a submission directory.
    """

    def __init__(self, mark_scheme: markscheme.MarkingScheme):
        """
        Constructor.
        """
        self.mark_scheme = mark_scheme
        self.submissions = mark_scheme.get_submissions()
        self.db = mark_scheme.get_db()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.at_exit = [self.temporary_directory.cleanup]
        self.path = Path(self.temporary_directory.name)

    def grade_submission(self, sub: submission.Submission):
        """
        Run the grader tests on a submission.
        """
        self.mark_scheme.run(sub)
        self.db.insert(
            sub.reference,
            sub.percentage,
            sub.generate_report(),
        )

    def grade_submissions(self):
        """
        Run the grader.
        """
        # TODO: Change to initial runtime database + post processing
        for sub in self.submissions:
            # noinspection PyBroadException
            try:
                self.grade_submission(sub)
            except Exception:
                type_, val, tb = sys.exc_info()
                print(
                    f'Error marking {sub.reference}\n'
                    f'{type_.__name__}: {val}'
                )
                traceback.print_tb(tb)
                continue


    # context manager
    def __enter__(self):
        os.chdir(self.path)
        return self

    def __exit__(self, err_type: Type[Exception], err_val: Type[Exception],
                 tb:Type):
        for fn in self.at_exit:
            fn()
