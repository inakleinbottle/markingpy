import logging
import warnings
import getpass
import hashlib
from contextlib import contextmanager
from pathlib import Path

from .config import GLOBAL_CONF
from .exercise import Exercise
from .linter import linter
from .utils import build_style_calc, log_calls
from .storage import get_db

logger = logging.getLogger(__name__)


class NotAMarkSchemeError(Exception):
    pass


def mark_scheme(**params):
    """
    Create a marking scheme config.py object.

    :param params:
    :return:
    """
    conf = dict(GLOBAL_CONF["markscheme"])
    conf.update(**params)
    return MarkschemeConfig(**conf)


@log_calls
def import_markscheme(path):
    """
    Import the marking scheme from path.

    :param path: Path to import
    :return: markscheme
    """
    if not path.name.endswith('.py'):
        raise NotAMarkSchemeError

    with open(path, "rt") as f:
        source = f.read()
    code = compile(source, path, "exec")
    ns = {}
    exec(code, ns)

    exercises = [ex for ex in ns.values() if isinstance(ex, Exercise)]
    try:
        config = [
            cf for cf in ns.values() if isinstance(cf, MarkschemeConfig)
        ][0]
    except IndexError:
        if not exercises:
            raise NotAMarkSchemeError
        config = MarkschemeConfig()
    return MarkingScheme(path, exercises, **config)


class MarkschemeConfig(dict):
    pass


class MarkingScheme:
    """
    Marking scheme class.
    """

    def __init__(
        self,
        path,
        exercises,
        style_formula=None,
        style_marks=10,
        score_style="basic",
        submission_path=None,
        marks_db=None,
        **kwargs
    ):
        self.path = path
        content = f'{str(path)},{getpass.getuser()}'.encode()
        self.unique_id = hashlib.md5(content).hexdigest()
        logger.info('The unique identifier for this '
                    f'markscheme is {self.unique_id}')
        self.exercises = exercises
        self.style_marks = style_marks
        self.score_style = score_style
        self.linter = linter
        self.style_calc = build_style_calc(style_formula)
        self.submission_path = submission_path
        self.marks_db = Path(marks_db).expanduser()

        # Unused parameters
        for k in kwargs:
            warnings.warn(f"Unrecognised option {k}")

    def update_config(self, args):
        for k, v in args.items():
            if v is None:
                continue

            if not hasattr(self, k):
                continue

            setattr(self, k, v)

    def get_submissions(self):
        path = (
            Path(self.submission_path)
            if self.submission_path is not None
            else Path(".", "submissions")
        )

        if not path.is_dir():
            raise NotADirectoryError(f"{path} is not a directory")

        for pth in path.iterdir():
            if not pth.is_file() or not pth.suffix == ".py":
                continue
            yield pth

    def get_db(self):
        return get_db(self.marks_db, self.unique_id)

    def format_return(self, score, total_score):
        """
        Format the returned score.

        :param score:
        :param total_score:
        :return: Formatted score
        """
        percentage = round(100 * score / total_score)
        if self.score_style == "basic":
            return str(score)
        elif self.score_style == "percentage":
            return f"{percentage}%"
        elif self.score_style == "marks/total":
            return f"{score} / {total_score}"
        elif self.score_style == "all":
            return f"{score} / {total_score} ({percentage}%)"
        else:
            return self.score_style.format(score=score,
                                           total=total_score,
                                           percentage=percentage)

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
        for mark, total_marks, feedback in (
            ex.run(ns) for ex in self.exercises
        ):
            score += mark
            total_score += total_marks
            report.append(feedback)
        submission.add_feedback("tests", "\n".join(report))

        lint_report = self.linter(submission)

        style_score = round(self.style_calc(lint_report) * self.style_marks)
        score += style_score
        total_score += self.style_marks
        style_feedback = [lint_report.read(),
                          f'Style score: {style_score} / {self.style_marks}']

        submission.add_feedback("style", '\n'.join(style_feedback))
        submission.percentage = round(100 * score / total_score)
        submission.score = self.format_return(score, total_score)
