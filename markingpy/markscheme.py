
import logging
import warnings
from contextlib import contextmanager
from pathlib import Path

from .config import GLOBAL_CONF
from .exercise import Exercise
from .linter import linter
from .utils import build_style_calc, log_calls


logger = logging.getLogger(__name__)


def mark_scheme(**params):
    """
    Create a marking scheme config.py object.

    :param params:
    :return:
    """
    return MarkschemeConfig(**params)


@log_calls
def import_markscheme(path):
    """
    Import the marking scheme from path.

    :param path: Path to import
    :return: markscheme
    """
    with open(path, 'rt') as f:
        source = f.read()
    code = compile(source, path, 'exec')
    ns = {}
    exec(code, ns)

    exercises = [ex for ex in ns.values() if isinstance(ex, Exercise)]
    try:
        config = [cf for cf in ns.values()
                  if isinstance(cf, MarkschemeConfig)][0]
    except IndexError:
        config = MarkschemeConfig()
    return MarkingScheme(exercises, **config.config)


class MarkschemeConfig:

    def __init__(self, **kwargs):
        self.config = kwargs


class MarkingScheme:
    """
    Marking scheme class.
    """

    def __init__(self, exercises, style_formula=None, style_marks=10,
                 score_style='real', submission_path=None,
                 **kwargs):
        self.exercises = exercises
        self.style_marks = style_marks
        self.score_style = score_style
        self.linter = linter
        if style_formula is None:
            style_formula = GLOBAL_CONF['grader']['style_formula']
        self.style_calc = build_style_calc(style_formula)
        self.submission_path = submission_path

        # Unused parameters
        for k in kwargs:
            warnings.warn('Unrecognised option {}'.format(k))

    def get_submissions(self):
        path = (Path(self.submission_path) if self.submission_path is not None
                else Path('.', 'submissions'))

        if not path.is_dir():
            raise NotADirectoryError('{} is not a directory'.format(path))

        for pth in path.iterdir():
            if not pth.is_file() or not pth.suffix == '.py':
                continue
            yield pth

    def format_return(self, score, total_score):
        """
        Format the returned score.

        :param score:
        :param total_score:
        :return: Formatted score
        """
        if self.score_style == 'real':
            return str(score)
        elif self.score_style == 'percentage':
            return '{}%'.format(round(100*score/total_score))
        elif self.score_style == 'marks/total':
            return '{} / {}'.format(score, total_score)
        elif self.score_style == 'all':
            return '{} / {} ({}%)'.format(score, total_score,
                                          round(100*score/total_score))

    def patched_import(self):
        def patched(*args, **kwargs):
            pass
        return patched

    @contextmanager
    def sandbox(self, ns):
        try:
            yield
        finally:
            pass

    @log_calls
    def run(self, submission):
        """
        Grade a submission.

        :param submission: Submission to grade
        """
        code = submission.compile()
        ns = {}
        with self.sandbox(ns):
            exec(code, ns)

        score = 0
        total_score = 0
        report = []
        for mark, total_marks, feedback in (ex.run(ns)
                                            for ex in self.exercises):
            score += mark
            total_score += total_marks
            report.append(feedback)
        submission.add_feedback('tests', '\n'.join(report))

        lint_report = self.linter(submission)

        style_score = round(self.style_calc(lint_report)*self.style_marks)
        score += style_score
        total_score += self.style_marks
        submission.add_feedback('style', lint_report.read())

        submission.score = self.format_return(score, total_score)




