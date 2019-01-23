"""
Grading tool for python files.
"""


import logging
import os
import sys
import tempfile
import traceback

from pathlib import Path

logger = logging.getLogger(__name__)
__all__ = ['Grader']


class Grader:
    """
    Grader object drives the grading for a submission directory.
    """

    def __init__(self, markscheme):
        """
        Constructor.
        """
        self.markscheme = markscheme
        self.submissions = markscheme.get_submissions()
        self.db = markscheme.get_db()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.at_exit = [self.temporary_directory.cleanup]
        self.path = Path(self.temporary_directory.name)

    def grade_submission(self, submission):
        """
        Run the grader tests on a submission.
        """
        self.markscheme.run(submission)
        self.db.insert(
            submission.reference,
            submission.percentage,
            submission.generate_report(),
        )

    def grade_submissions(self, **opts):
        """
        Run the grader.
        """
        # TODO: Change to initial runtime database + post processing
        for submission in self.submissions:
            # noinspection PyBroadException
            try:
                self.grade_submission(submission)
            except Exception:
                type_, val, tb = sys.exc_info()
                print(
                        f'Error marking {submission.reference}\n'
                        f'{type_.__name__}: {val}'
                        )
                traceback.print_tb(tb)
                continue

    # context manager
    def __enter__(self):
        os.chdir(self.path)
        return self

    def __exit__(self, err_type, err_val, tb):

        for fn in self.at_exit:
            fn()
