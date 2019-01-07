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
        self.compiler = Compiler()
        self.code = None
        self.score = None
        self.feedback = {}

    def compile(self):
        """
        Compile the submission source code.
        """
        if not self.code:
            self.code = self.compiler(self.source)
            self.add_feedback('compilation',
                              '\n'.join((c.content + '\n' + repr(c.get_first_error().exc)
                                        for c in self.compiler.removed_chunks)))
        return self.code

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
