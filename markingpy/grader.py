"""
Grading tool for python files.
"""

import sys
import logging

from os import listdir
from os.path import join as pathjoin


from .submission import Submission
from .storage import write_csv
from .markscheme import import_markscheme


logger = logging.getLogger(__name__)


class Grader:
    """
    Grader object drives the grading for a submission directory.
    """

    def __init__(self, directory, test_file):
        """
        Constructor.
        """
        self.directory = directory
        markscheme = self.markscheme = import_markscheme(test_file)
        # self.submissions = [Submission(pathjoin(directory, path))
        #                     for path in listdir(directory)
        #                     if path.endswith('.py')]
        self.submissions = (Submission(pth) for pth in markscheme.get_submissions())
        self.at_exit = []

    def grade_submission(self, submission, **opts):
        """
        Run the grader tests on a submission.
        """
        self.markscheme.run(submission)

    def dump_to_csv(self, path):
        """
        Write summary statistics to csv file.
        """
        write_csv(path, self.submissions)

    def grade_submissions(self, **opts):
        """
        Run the grader.
        """
        #TODO: Change to initial runtime database + post processing
        directory = opts['out']
        for submission in self.submissions:
            self.grade_submission(submission, **opts)
            with open(pathjoin(directory,
                               submission.reference + '.txt'), 'w') as f:
                f.write(submission.generate_report())

            if opts['print']:
                print(f'Submission {submission.reference}: {submission.score}')



    # context manager

    def __enter__(self):
        sys.path.insert(0, self.directory)
        return self

    def __exit__(self, *args, **kwargs):
        sys.path.remove(self.directory)
        for fn in self.at_exit:
            fn()


