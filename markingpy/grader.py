"""
Grading tool for python files.
"""

import sys
import logging

from os import listdir
from os.path import join as pathjoin
from unittest import TextTestRunner
from io import StringIO


from .testcases import load_tests, TestResult
from .submission import Submission
from .linter import linter
from .storage import write_csv
from .email import EmailSender
from .utils import build_style_calc, test_calculator
from .exercise import run_tests

logger = logging.getLogger(__name__)



class Grader:
    """
    Grader object drives the grading for a submission directory.
    """

    def __init__(self, directory, test_file, config):
        """
        Constructor.
        """
        self.directory = directory
        self.config = config
        with open(test_file) as f:
            self.tests = compile(f.read(), test_file, 'exec')
        
        # first pass to populate global options
        args = {}
        exec(self.tests, args)
        #logger.info(args)
        self.weighting = args['scheme']
        formula = config['grader']['style_formula']
        self.style_calc = build_style_calc(formula)
        self.submissions = [Submission(pathjoin(directory, path))
                            for path in listdir(directory)
                            if path.endswith('.py')]

        self.linter = linter
        self.at_exit = []
        
        

    def grade_submission(self, submission, **opts):
        """
        Run the grader tests on a submission.
        """
        submission.compile()
        # linter
        submission.run_test('style', 
                            lambda s: self.linter(s),
                            self.style_calc,
                            self.weighting['style'])
        
        # tests
        submission.run_test('test',
                            lambda s: run_tests(self.tests, s),
                            test_calculator, 
                            self.weighting['test'])

    def dump_to_csv(self, path):
        """
        Write summary statistics to csv file.
        """
        write_csv(path, self.submissions)

    def grade_submissions(self, **opts):
        """
        Run the grader.
        """


        for submission in self.submissions:
            self.grade_submission(submission, **opts)

        if opts['csv'] is not None:
            self.dump_to_csv(opts['csv'])
        elif opts['out'] is not None:
            directory = opts['out']
            for sub in self.submissions:
                with open(pathjoin(directory, 
                                   sub.reference + '.txt'), 'w') as f:
                    f.write(sub.generate_report())
        elif opts['print']:
            for submission in self.submissions:
                print(f'Submission {submission.reference}: {submission.score}')

    # context manager

    def __enter__(self):
        sys.path.insert(0, self.directory)
        return self

    def __exit__(self, *args, **kwargs):
        sys.path.remove(self.directory)
        for fn in self.at_exit:
            fn()


if __name__ == '__main__':
    tests = 'scheme.py'
    with Grader(sys.argv[1], tests) as grader:
        grader.grade_submissions()
