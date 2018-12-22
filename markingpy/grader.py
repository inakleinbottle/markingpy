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
        self.submissions = [Submission(pathjoin(directory, path), **config['submission'])
                            for path in listdir(directory)
                            if path.endswith('.py')]
        with open(test_file) as f:
            self.tests = compile(f.read(), test_file, 'exec')

        self.linter = linter
        self.mailsender = None
        self.at_exit = []

    def grade_submission(self, submission, **opts):
        """
        Run the grader tests on a submission.
        """
        # lint first, catch syntax errors
        report = self.linter(submission.path)
        submission.add_feedback('style', report)

        # safe to compile submission
        submission.compile()

        tests = load_tests(self.tests, submission.globals)

        stream = StringIO()
        result = TextTestRunner(
            stream=stream, resultclass=TestResult).run(tests)
        submission.add_feedback('test', result)

        report = submission.generate_report()
        if 'out' in opts and opts['out'] is not None:
            out_path = pathjoin(opts['out'], submission.reference + '.txt')
            with open(out_path, 'w') as f:
                f.write(report)

        if self.mailsender and submission.mailto:
            self.mailsender.create_mail(submission.mailto,
                                        'Submission results',
                                        report)

    def dump_to_csv(self, path):
        """
        Write summary statistics to csv file.
        """
        write_csv(path, self.submissions)

    def grade_submissions(self, **opts):
        """
        Run the grader.
        """
        if opts['mail']:
            sender = self.config['email']['sender']
            username = self.config['email']['username']
            host = self.config['email']['host']
            port = int(self.config['email']['port'])
            self.mailsender = EmailSender(sender,
                                          username=username,
                                          server_addr=(host, port))
            self.at_exit.append(self.mailsender.quit)

        for submission in self.submissions:
            self.grade_submission(submission, **opts)

        if opts['csv'] is not None:
            self.dump_to_csv(opts['csv'])

        if self.mailsender:
            self.mailsender.authenticate()
            self.mailsender.send_all()

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
