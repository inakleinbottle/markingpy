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


from . import finders

logger = logging.getLogger(__name__)


class NotAMarkSchemeError(Exception):
    pass


class MarkschemeError(Exception):
    pass


def mark_scheme(**params):
    """
    Create a marking scheme config.py object.

    :param marks: Total marks available for this coursework.

        .. versionadded:: 0.2.0
    :param submission_path:
        Path to submissions. See note below.
    :param finder: :class:`markingpy.finders.BaseFinder` instance that
        should be used to generate submissions. The *finder* option takes
        precedence over *submission path* if provided. If neither is provided,
        the default ::

            markingpy.finders.DirectoryFinder('submissions')

        is used.

        .. versionadded:: 0.2.0
    :param style_marks: Number of marks available for coding style.
    :param style_formula: Formula used to generate a score from the linter
        report.
    :param score_style: Formatting style for marks to be displayed in feedback.
        Can be a choice of one of the builtin options: 'basic' (default);
        'percentage'; 'marks/total'; 'all' marks/total (percentage).
        Alternatively, a format string can be provided with the variables
        *mark*, *total*, and *percentage*. For example, the 'all' builtin is
        equivalent to ``'{mark}/{total} ({percentage})'``.
    :param marks_db: Path to database to store submission results and feedback.
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
    if not path.name.endswith(".py"):
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

    marking_scheme = MarkingScheme(path, exercises, **config)
    marking_scheme.validate()
    return marking_scheme


class MarkschemeConfig(dict):
    pass


class MarkingScheme:
    """
    Marking scheme class.

    :param marks: Total marks available for this coursework. If provided,
        this is used to validate the markscheme.

        .. versionadded:: 0.2.0
    :type marks: int
    :param submission_path:
        Path to submissions. See note below.
    :param finder: :class:`markingpy.finders.BaseFinder` instance that
        should be used to generate submissions. The *finder* option takes
        precedence over *submission path* if provided. If neither is provided,
        the default ::

            markingpy.finders.DirectoryFinder('submissions')

        is used.

        .. versionadded:: 0.2.0
    :param style_marks: Number of marks available for coding style.
    :param style_formula: Formula used to generate a score from the linter
        report.
    :param score_style: Formatting style for marks to be displayed in feedback.
        Can be a choice of one of the builtin options: 'basic' (default);
        'percentage'; 'marks/total'; 'all' marks/total (percentage).
        Alternatively, a format string can be provided with the variables
        *mark*, *total*, and *percentage*. For example, the 'all' builtin is
        equivalent to ``'{mark}/{total} ({percentage})'``.
    :param marks_db: Path to database to store submission results and feedback.
    """

    def __init__(
        self,
        path,
        exercises,
        marks=None,
        style_formula=None,
        style_marks=10,
        score_style="basic",
        submission_path=None,
        finder=None,
        marks_db=None,
        **kwargs,
    ):
        self.path = path
        content = f"{str(path)},{getpass.getuser()}".encode()
        self.unique_id = hashlib.md5(content).hexdigest()
        logger.info(
            "The unique identifier for this " f"markscheme is {self.unique_id}"
        )
        self.marks = marks
        self.exercises = exercises
        self.style_marks = style_marks
        self.score_style = score_style
        self.linter = linter
        self.style_calc = build_style_calc(style_formula)

        # Set up the finder for loading submissions.
        if finder is None and submission_path is None:
            self.finder = finders.DirectoryFinder(Path(".", "submissions"))
        elif finder is None and submission_path:
            self.finder = finders.DirectoryFinder(submission_path)
        elif isinstance(finder, finders.BaseFinder):
            self.finder = finder
        else:
            raise TypeError(
                "finder must be an be an instance of a subclass "
                "of markingpy.finders.BaseFinder"
            )

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

    def validate(self):
        logger.debug('Validating Markscheme')
        for ex in self.exercises:
            # ExerciseError raised if any exercise fails to validate
            # This also locks all exercises into submission mode.
            ex.validate()
            logger.debug(f'Validation of {ex.name}: Passed')

        if self.marks is not None:
            # If validation marks parameter provided, validate the mark totals
            marks_from_ex = sum(ex.marks for ex in self.exercises)
            style_marks = self.style_marks
            total_marks_for_ms = marks_from_ex + style_marks
            if not total_marks_for_ms == self.marks:
                raise MarkschemeError(
                    f'Total marks available in marking scheme '
                    f'({total_marks_for_ms}) do not match the marks allocated '
                    f'in the marking scheme configuration ({self.marks})'
                )
            logger.debug(f'Marking validation: Passed')

    def get_submissions(self):
        yield from self.finder.get_submissions()

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
            return self.score_style.format(
                score=score, total=total_score, percentage=percentage
            )

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
        style_feedback = [
            lint_report.read(),
            f"Style score: {style_score} / {self.style_marks}",
        ]

        submission.add_feedback("style", "\n".join(style_feedback))
        submission.percentage = round(100 * score / total_score)
        submission.score = self.format_return(score, total_score)
