#      Markingpy automatic grading tool for Python code.
#      Copyright (C) 2019 University of East Anglia
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#
import importlib
import importlib.util
import logging
import warnings

from inspect import isclass, isfunction
from pathlib import Path
from typing import ( Optional, Type, Dict, Tuple, Any, TYPE_CHECKING, Union)

from .import finders
from .import storage
from .import grader as _grader
from .import execution
from .import exercises

from .utils import log_calls

if TYPE_CHECKING:
    import importlib.machinery
    from .import syntax
ARGS = Tuple[Any, ...]
KWARGS = Dict[str, Any]
logger = logging.getLogger(__name__)
__all__ = ['MarkingScheme', 'NotAMarkSchemeError', 'MarkingSchemeError']


class NotAMarkSchemeError(Exception):
    pass


class MarkingSchemeError(Exception):
    pass


def get_spec_path_or_module(
    name: Union[str, Path], modname: str = 'markingpy_marking_scheme'
) -> Optional[importlib.machinery.ModuleSpec]:
    path = Path(name).resolve()
    if path.exists():
        return importlib.util.spec_from_file_location(modname, location=path)

    spec = importlib.util.find_spec(name)
    if spec is None:
        return spec

    spec.name = modname
    return spec


class SubmissionLoadError(Exception):
    pass




# noinspection PyUnresolvedReferences
class MarkingScheme:
    """
    Marking scheme class.

    :param marks: Total marks available for this coursework. If provided,
        this is used to validate the markscheme.
    :type marks: int
    :param submission_path:
        Path to submissions. See note below.
    :param finder: :class:`markingpy.finders.BaseFinder` instance that
        should be used to generate submissions. The *finder* option takes
        precedence over *submission path* if provided. If neither is provided,
        the default ::

            markingpy.finders.DirectoryFinder('submissions')

        is used.
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
        marks: Optional[int] = None,
        score_style: str = "basic",
        grader=None,
        submission_path: Optional[str] = None,
        finder: Optional[finders.BaseFinder] = None,
        linter: Optional['syntax.CodeStyleCheckerABC'] = None,
        marks_db: Optional[storage.StorageABC] = None,
        preload_modules: Optional[list] = None,
        **kwargs: Any,
    ):
        # Set up variables
        self.marks = marks
        self.score_style = score_style
        self.preload_modules = preload_modules if preload_modules else []
        if marks_db is None:
            marks_db = storage.CSVStorageDB(Path("marks.csv"))
        self.db = marks_db
        # Initialise exercise list
        self.exercises = []
        # set up the grader
        self.grader = grader if grader else _grader.SimpleGrader()
        # Set up the linter - can be None
        self.linter = linter
        # Set up the finder for loading submissions.
        if finder is None and submission_path is None:
            self.finder = finders.DirectoryFinder(Path(".", "submissions"))
        elif finder is None and submission_path:
            pth = Path(submission_path).resolve()
            self.finder = finders.DirectoryFinder(pth)
        elif isinstance(finder, finders.BaseFinder):
            self.finder = finder
        else:
            self.finder = None
        # Unused parameters
        for k in kwargs:
            warnings.warn(f"Unrecognised option {k}")

    def update_config(self, args: KWARGS):
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
        logger.info('Validating Markscheme')
        for ex in self.exercises:
            # ExerciseError raised if any exercise fails to validate
            # This also locks all exercises into submission mode.
            try:
                ex.validate()
            except exercises.ExerciseError as err:
                logger.error(f'Failed to validate {str(ex)}')
                raise MarkingSchemeError from err

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

        logger.info(f'Marking validation: Passed')

    def add_exercise(self, exercise: 'exercises.ExerciseBase'):
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
        if self.finder is None:
            raise RuntimeError('No submission finder provided.')

        yield from self.finder.get_submissions()

    def format_return(self, score: int, total_score: int) -> str:
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

    def exercise(
        self,
        name: Optional[str] = None,
        cls: Type[exercises.Exercise] = None,
        interactive: bool = False,
        **args: Any,
    ) -> exercises.Exercise:
        """
        Create a new exercise using this function or class as the model solution.

        The decorated function or class will be wrapped by an Exercise object that
        behaves like the original object.

        Keyword arguments are forwarded to the Exercise instance.

        :param interactive:
        :param name: Name for the exercise.
        :type name: str
        :param cls: The exercise class to be instantiated. Defaults to
            :class:`FunctionExercise` if a function is decorated and
            :class:`ClassExercise` if a class is decorated.
        :param submission_name: Name of function or class to find in submission
            namespace.
        :type cls: :class:`Exercise`
        """
        if isinstance(name, str):
            args["name"] = name
            name = None

        def decorator(fn):
            nonlocal cls
            if cls is None and isfunction(fn):
                cls = exercises.FunctionExercise
            elif cls is None and isclass(fn) and interactive:
                cls = exercises.InteractionExercise
            elif cls is None and isclass(fn):
                cls = exercises.ClassExercise
            else:
                raise TypeError("Expecting function or class.")

            ex = cls(fn, **args)
            self.add_exercise(ex)
            return ex

        if name is None:
            return decorator

        else:
            return decorator(name)

    def create_grading_task(self):
        """
        Create the grading task to run in the grader.

        :return:
        """
        return execution.TestRun(self.exercises, self.preload_modules)

    @log_calls
    def run(self, generate=False):
        """
        Grade the submissions.

        :param generate: If true is passed, each submission will be passed
        to the caller via a yield. Default False.
        """
        grader = self.grader
        grader.set_db(self.db)
        linter = self.linter
        task = self.create_grading_task()
        for sub in self.get_submissions():
            if linter:
                lint_report = linter.check(sub)
                sub.add_feedback('style', lint_report)
            grader.submit(task, sub)
            if generate:
                yield sub
