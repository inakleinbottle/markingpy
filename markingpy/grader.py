"""
Grading tool for python files.
"""

import sys
import logging
from pathlib import Path
from .submission import Submission


logger = logging.getLogger(__name__)


class Grader:
    """
    Grader object drives the grading for a submission directory.
    """

    def __init__(self, markscheme):
        """
        Constructor.
        """
        self.markscheme = markscheme
        self.submissions = (
            Submission(pth) for pth in markscheme.get_submissions()
        )
        self.db = markscheme.get_db()
        self.at_exit = []

    def grade_submission(self, submission, **opts):
        """
        Run the grader tests on a submission.
        """
        self.markscheme.run(submission)
        self.db.insert(submission.reference,
                       submission.percentage,
                       submission.generate_report())

    def grade_submissions(self, **opts):
        """
        Run the grader.
        """
        # TODO: Change to initial runtime database + post processing
        for submission in self.submissions:
            self.grade_submission(submission, **opts)

    # context manager
    def __enter__(self):
        sys.path.insert(0, self.markscheme.submission_path)
        return self

    def __exit__(self, err_type, err_val, tb):
        sys.path.remove(self.markscheme.submission_path)
        for fn in self.at_exit:
            fn()
