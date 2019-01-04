
import logging
import warnings

from markingpy import GLOBAL_CONF
from .exercise import Exercise
from .linter import linter
from .utils import build_style_calc


def mark_scheme(**params):
    """
    Create a marking scheme config object.

    :param params:
    :return:
    """
    return MarkschemeConfig(**params)


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
                 score_style='real',
                 **kwargs):
        self.exercises = exercises
        self.style_marks = style_marks
        self.score_style = score_style
        self.linter = linter
        if style_formula is None:
            style_formula = GLOBAL_CONF['grader']['style_formula']
        self.style_calc = build_style_calc(style_formula)

        # Unused parameters
        for k in kwargs:
            warnings.warn('Unrecognised option {}'.format(k))

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

    def run(self, submission):
        """
        Grade a submission.

        :param submission: Submission to grade
        """
        score = 0
        total_score = 0
        report = []
        for mark, total_marks, feedback in (ex.run(submission.globals)
                                            for ex in self.exercises):
            score += mark
            total_score += total_marks
            report.append(feedback)
        submission.add_feedback('tests', '\n'.join(report))

        lint_report = self.linter(submission)
        score += round(self.style_calc(lint_report)*self.style_marks)
        total_score += self.style_marks
        submission.add_feedback('style', lint_report.read())

        submission.score = self.format_return(score, total_score)




