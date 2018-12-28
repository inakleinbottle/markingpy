import os
import logging
from io import StringIO

from markingpy.compiler import Compiler

logger = logging.getLogger(__name__)


class Submission:

    def __init__(self, path, **kwargs):
        self.path = path
        with open(path, 'r') as f:
            self.source = f.read()
        self.reference = os.path.splitext(os.path.basename(path))[0]
        self.globals = {}
        self.compiler = Compiler()
        self.feedback = {}
        self.compiled = False
        self.weighting = {}
        self.scores = {}

    @property
    def score(self):
        return round(sum(self.get_weighted_score(k)
                         for k in self.weighting))

    def set_score(self, score_type, calc):
        self.scores[score_type] = calc(self.feedback[score_type])
        logger.info(f'Setting score: {self.scores[score_type]}')

    def get_score(self, score_type):
        return self.scores.get(score_type, 0)

    def get_weighted_score(self, score_type):
        return self.get_score(score_type)*self.weighting[score_type]

    def compile(self):
        """
        Compile the submssion source code.
        """
        if not self.compiled:
            code = self.compiler(self.source)
            exec(code, self.globals)
            self.add_feedback('compilation',
                              self.compiler.report)
            self.compiled = True

    def add_feedback(self, item, feedback):
        """
        Add feedback to the submission.
        """
        self.feedback[item] = feedback

    def run_test(self, ref, test, calc, weight):
        """
        Run a test on the submission
        """
        logger.info(f'Running test: {self.reference} : {ref} : {weight}')
        result = test(self)
        self.weighting[ref] = weight
        self.add_feedback(ref, result)
        self.set_score(ref, calc)

    def generate_report(self):
        """
        Generate report for this submission.
        """
        lines = []
        lines.append('Result summary for submission %s' % self.reference)
        test_report = self.feedback.get('test', None)
        style_report = self.feedback.get('style', None)

        if test_report is not None:
            lines.append('\nResults of test cases')
            for result, test, err in test_report.all_tests:
                lines.append('%s: %s' %
                             (result, test_report.getDescription(test)))
        if style_report is not None:
            lines.append('\nResults of style analysis')
            lines.append(style_report.read())

        lines.append('\n' + '=' * 70 + '\n' + 'Final score: %s%%' % self.score)
        return '\n'.join(lines)
