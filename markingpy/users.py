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
"""
User level functions for creating marking schemes and exercises.
"""
from pathlib import Path
from typing import Any, Optional, Type


from .import markscheme
from .import config
from .import exercises
from .import storage

__all__ = ['mark_scheme', 'exercise']
_MARKSCHEME = None


def mark_scheme(**params: Any) -> markscheme.MarkingScheme:
    """
    Create or update a marking scheme.

    The marking scheme object is responsible for delegating marking tasks and
    handling creation of exercises. Multiple calls to this function will yield
    the same marking scheme object, although the configuration will be updated
    with new values when on multiple calls.

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
    global _MARKSCHEME
    if _MARKSCHEME is None:
        conf = dict(config.GLOBAL_CONF["markscheme"])
        if 'marks_db' in conf:
            conf['marks_db'] = storage.SQLiteDB(Path(conf['marks_db']))
        conf.update(**params)
        marking_scheme = markscheme.MarkingScheme(**conf)
        _MARKSCHEME = marking_scheme
    else:
        marking_scheme = _MARKSCHEME
        marking_scheme.update_config(params)
    return marking_scheme


def exercise(
    name: Optional[str] = None,
    cls: Type[exercises.Exercise] = None,
    interactive: bool = False,
    **args: Any,
) -> exercises.Exercise:
    """
    Create a new exercise using this function or class as the model solution.

    Equivalent to first creating a marking scheme and then using the attached
    exercise decorator. If no marking scheme exists, one is created with the
    default configuration.

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
    # Import mark_scheme here to prevent circular imports
    ms = mark_scheme()
    return ms.exercise(name, cls, interactive, **args)
