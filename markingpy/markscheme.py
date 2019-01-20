import builtins
import hashlib
import importlib.util
import inspect
import logging
import sys
import warnings

from builtins import __import__
from collections import ChainMap
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

from . import finders

from .config import GLOBAL_CONF
from .exercises import Exercise
from .linters import linter
from .utils import build_style_calc, log_calls
from .storage import get_db


logger = logging.getLogger(__name__)

__all__ = [
    'MarkingScheme',
    'NotAMarkSchemeError',
    'MarkschemeError',
    'MarkschemeConfig',
    'mark_scheme',
    'get_markscheme',
    'set_markscheme',
]

_MARKSCHEME = None


def get_markscheme():
    if _MARKSCHEME is None:
        raise RuntimeError('Markscheme has not been created.')

    return _MARKSCHEME


def set_markscheme(markscheme):
    global _MARKSCHEME
    if _MARKSCHEME is not None:
        raise RuntimeError('Markscheme already created.')

    _MARKSCHEME = markscheme


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
    conf = MarkschemeConfig(GLOBAL_CONF["markscheme"])
    conf.update(**params)
    marking_scheme = MarkingScheme(**conf)
    set_markscheme(marking_scheme)
    return conf


def get_spec_path_or_module(name, modname='markingpy_marking_scheme'):
    path = Path(name)
    if path.is_file():
        return importlib.util.spec_from_file_location(modname, str(path))

    spec = importlib.util.find_spec(name)
    spec.name = modname
    return spec


# noinspection PyNoneFunctionAssignment
@log_calls
def import_markscheme(path):
    """
    Import the marking scheme from path.

    :param path: Path to import
    :return: markscheme
    """
    spec = get_spec_path_or_module(path)
    if spec is None:
        raise MarkschemeError(f'Could not locate marking scheme: {path}')

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules[mod.__name__] = mod
    marking_scheme = get_markscheme()
    return marking_scheme


class MarkschemeConfig(dict):
    pass


class ForbiddenImportError(ImportError):
    pass


class ForbiddenFunctionCall(RuntimeError):
    pass


class WrappedModule:
    """
    Wrapper around module types to control access to certain attributes.
    """

    def __init__(self, mod):
        self.mod = mod
        self.__name__ = mod.__name__
        self.__doc__ = mod.__doc__
        self.__loader__ = mod.__loader__
        self.__package__ = mod.__package__

    def __repr__(self):
        return repr(self.mod)

    def __str__(self):
        return str(self.mod)

    def __getattr__(self, item):
        return getattr(self.mod, item)


class ControlledFunction:
    """
    Wrapper for builtin functions to control their execution in sandbox.
    """

    def __init__(self, func):
        wraps(func)(self)
        self.func = func
        self.allowed = False

    @contextmanager
    def restore(self):
        self.allowed = True
        try:
            yield
        finally:
            self.allowed = False

    def __call__(self, *args, **kwargs):
        if not self.allowed:
            raise ForbiddenFunctionCall
        self.func(*args, **kwargs)


class ModuleList(dict):
    """
    Specialised dictionary that wraps modules added to the list.
    """
    wrapper_class = WrappedModule

    def __setitem__(self, name, val):
        super().__setitem__(name, WrappedModule(val))


class Importer:
    """
    Import wrapper for executing code in a sandbox.

    Allows setting allowed list and forbidden lists, and keeps track of the
    modules that are imported. All imported modules are wrapped with
    :class:`ModuleWrapper`, which can be customised to allow or disallow
    access to certain attributes in a module.
    """

    def __init__(self, allowed=None, forbidden=None,
                 import_=None, eval_=None, exec_=None):
        self.allowed = allowed if allowed else []
        self.forbidden = forbidden if forbidden else []
        self.eval_ = eval_
        self.exec_ = exec_
        self.loaded_modules = ModuleList()
        self.import_ = import_ or __import__

    def _is_forbidden(self, name):
        return name in self.forbidden

    def _is_not_allowed(self, name):
        return name not in self.allowed

    def __call__(self, name, *args):
        if self._is_forbidden(name):
            raise ForbiddenImportError(
                f'Importing {name} is forbidden'
            )
        if self._is_not_allowed(name):
            warnings.warn(
                f'User import module {name}'
            )
        if name not in self.loaded_modules:
            with self.eval_.restore(), self.exec_.restore():
                self.loaded_modules[name] = self.import_(name, *args)
        return self.loaded_modules[name]


def prepare_namespace():
    """
    Prepare the namespace for a submission.

    Create a new namespace to be used to exec submission code. The standard
    builtins will be loaded with the ``__import__`` function replaced by a
    controlled importer, and ``exec`` and ``eval`` disabled.

    :return: namespace ``dict``, :class:`Importer`,
        :class:`ControlledFunction` ``eval``,
        :class:`ControlledFunction` ``exec``
    """
    ns = {'__builtins__': builtins.__dict__.copy()}
    eval_ = eval
    exec_ = exec
    c_eval = ControlledFunction(eval_)
    c_exec = ControlledFunction(exec_)
    importer = Importer(eval_=c_eval, exec_=c_exec)
    ns['__builtins__']['__import__'] = importer
    ns['__builtins__']['eval'] = c_eval
    ns['__builtins__']['exec'] = c_exec
    return ns, importer, c_eval, c_exec


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
        unique_id=None,
        marks=None,
        style_formula=None,
        style_marks=10,
        score_style="basic",
        submission_path=None,
        finder=None,
        marks_db=None,
        **kwargs,
    ):
        # Unique identifier - hash of path with user
        self.unique_id = unique_id

        # Set up variables
        self.marks = marks
        self.style_marks = style_marks
        self.score_style = score_style

        # Set the exercises
        self.exercises = Exercise.get_all_exercises()
        Exercise.set_marking_scheme(self)

        # Set up the linter
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

        # Database setup
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
        """
        Validate the marking scheme.

        Check that the marking scheme is valid by running the tests against
        the model solutions. The model solutions must attain maximum marks
        in order to be deemed valid.

        :raises: :class:`MarkingSchemeError` on validation failure.
        """
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

    def add_exercise(self, exercise):
        """
        Add an exercise to this marking scheme.

        :param exercise: :class:`Exercise` to add.
        """
        if exercise not in self.exercises:
            self.exercises.append(exercise)

    def get_submissions(self):
        """
        Get the submissions using the marking scheme finder.

        This is a generator.
        """
        yield from self.finder.get_submissions()

    def set_unique_id(self, module_name='markingpy_marking_scheme'):
        """
        Set the unique id for this marking scheme.

        By default, this is the hex digest of the MD5 hash of the marking
        scheme source file.

        :param module_name: name of the module to import
        """
        if not self.unique_id:
            mod = importlib.import_module(module_name)
            self.unique_id = hashlib.md5(inspect.getsource(mod)).hexdigest()

    def get_db(self):
        """
        Get the Marks database for this markingscheme. This uses the
        ``marks_db`` option set in the mark scheme setup or in the global
        configuration.

        :return: :class:`~markingpy.storage.Database` object
        """
        self.set_unique_id()
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

    @contextmanager
    def sandbox(self):
        """
        Create a sandbox to exec submission code in a context manager. This
        replaces ``sys.modules`` with a chain map so that imported modules will
        not have global effects. Upon exit, ``sys.modules`` is restored to
        its original state.
        """

        sys.modules = ChainMap({}, sys.modules)
        try:
            yield
        finally:
            sys.modules = sys.modules.maps[1]

    @log_calls
    def run(self, submission):
        """
        Grade a submission.

        :param submission: Submission to grade
        """
        code = submission.compile()
        ns, importer, c_eval, c_exec = prepare_namespace()

        with self.sandbox():
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
