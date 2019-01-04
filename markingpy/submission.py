import os
import logging


from markingpy.compiler import Compiler

logger = logging.getLogger(__name__)

INDENT = ' '*4


class Submission:

    def __init__(self, path, **kwargs):
        self.path = path
        with open(path, 'r') as f:
            self.source = f.read()
        self.reference = os.path.splitext(os.path.basename(path))[0]
        self.globals = {}
        self.compiler = Compiler()
        self.compiled = False
        self.score = None
        self.feedback = {}

    def set_score(self, score):
        self.score = score

    def compile(self):
        """
        Compile the submission source code.
        """
        if not self.compiled:
            code = self.compiler(self.source)
            exec(code, self.globals)
            self.add_feedback('compilation',
                              '\n'.join(self.compiler.removed_chunks))
            self.compiled = True

    def add_feedback(self, item, feedback):
        """
        Add feedback to the submission.
        """
        self.feedback[item] = feedback

    def generate_report(self):
        """
        Generate report for this submission.
        """
        lines = ['Result summary for submission {}'.format(self.reference),
                 '\nCompilation report:',
                 self.feedback.get('compilation', ''),
                 '\nResults for exercises:',
                 self.feedback.get('tests', ''),
                 '\nResults of style analysis:',
                 self.feedback.get('style', ''),
                 '\n' + '='*70 + '\n',
                 'Final score {}'.format(self.score),
                 ]

        return '\n'.join(lines)
