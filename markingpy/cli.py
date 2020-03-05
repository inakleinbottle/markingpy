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
"""Command line interface for MarkingPy."""
import importlib.util
import sys

import logging
import statistics
from argparse import ArgumentParser
from functools import partial
from pathlib import Path
import traceback


logger = logging.getLogger("markingpy")

from .import markscheme as _markscheme
from .import users
from .import finders


# noinspection PyNoneFunctionAssignment
def import_markscheme(path: Path) -> _markscheme.MarkingScheme:
    """
    Import the marking scheme from path.

    :param path: Path to import
    :return: markscheme
    """
    spec = _markscheme.get_spec_path_or_module(path)
    if spec is None:
        raise _markscheme.MarkingSchemeError(f'Could not locate marking '
                                              f'scheme: {path}')

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules[mod.__name__] = mod
    return users.mark_scheme()


class CLIError(Exception):
    pass


def run():
    """
    General markingpy cli
    """
    parser = ArgumentParser(
        description=("Markingpy grading tool."),
        usage=('markingpy [--verbose] [SCHEME|COMMAND] [OPTIONS]'),
        add_help=False,
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Run markingpy in verbose mode'
    )
    parser.add_argument('scheme_or_command', help='Marking scheme or command to use.')
    args, missed_args = parser.parse_known_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    cmd = args.scheme_or_command
    fn = getattr(TerminalCommands, cmd, None)
    if fn is None:
        return handle_marking_scheme(cmd, missed_args, parser)

    return fn(args)


class TerminalCommands:

    @staticmethod
    def create(args):
        parser = ArgumentParser(description='Create a new marking scheme')
        parser.add_argument('path', help='Path in which to create new marking scheme.')
        parser.parse_args(args)
        print('Creating new marking scheme')


def handle_marking_scheme(path, args, root_parser):
    # noinspection PyBroadException
    try:
        markscheme = import_markscheme(path)
    except Exception:
        traceback.print_exc()
        # root_parser.print_help()
        root_parser.exit()
    parser = ArgumentParser(usage=f'markingpy {path}')

    sub_parsers = parser.add_subparsers()
    run_parser = sub_parsers.add_parser(
        'run',
        help=(
            "Run the markingpy grader using the marking scheme "
            f"{path}. The grader will use the settings "
            f"defined in {path} along with any default "
            "values (set in .markingpy if this exists) or options "
            "passed to this command."
        ),
    )
    run_parser.add_argument(
        "--style-formula",
        type=str,
        help="Formula used to generate a score from the linter report.",
    )
    run_parser.add_argument(
        "--score-style", help="Formatting style for marks to be displayed in feedback."
    )
    run_parser.add_argument("--submission-path", type=str, help="Path to submissions.")
    run_parser.add_argument(
        "--marks-db",
        type=str,
        help="Path to database to store submission results and feedback.",
    )
    run_parser.add_argument(
        "--marks",
        type=int,
        help=(
            "Total marks available for this coursework."
            " This option is only used for validation."
        ),
    )
    run_parser.add_argument(
        "--target",
        type=str,
        default=None,
        help=("Target directory for checking."),
    )
    run_parser.set_defaults(func=partial(run_ms, markscheme))
    summary_parser = sub_parsers.add_parser(
        'summary',
        help=(
            "Print a summary of grades obtained in the last run of the "
            "grader with this marking scheme. This will load the "
            "results in the default database, the database specified in"
            f" {path} or the database specified in the options for "
            "this command."
        ),
    )
    summary_parser.add_argument(
        "--marks-db",
        type=str,
        help="Path to database to store submission results and feedback.",
    )
    summary_parser.set_defaults(func=partial(summary, markscheme))
    grades_parser = sub_parsers.add_parser(
        'grades',
        help=(
            "Print the grades obtained in the last run of the grader"
            "with this marking scheme. This will load the results in"
            "the default database, the database specified in "
            f"{path} or the database specified in the options for "
            "this command."
        ),
    )
    grades_parser.add_argument(
        "--marks-db",
        type=str,
        help="Path to database to store submission results and feedback.",
    )
    grades_parser.set_defaults(func=partial(grades, markscheme))
    dump_parser = sub_parsers.add_parser(
        'dump',
        help=(
            "Dump the feedback obtained in the last run of the "
            "grader with this marking scheme into the directory 'path'. "
            "This will load the results in the default database, "
            f"the database specified in {path} "
            "or the database specified in the options for "
            "this command."
        ),
    )
    dump_parser.add_argument(
        "--marks-db",
        type=str,
        help="Path to database to store submission results and feedback.",
    )
    dump_parser.add_argument(
        "path", default=".", nargs="?", help="Directory to populate with feedback."
    )
    dump_parser.set_defaults(func=partial(dump, markscheme))
    validate_parser = sub_parsers.add_parser(
        'validate',
        help=(
            'Validate the marking scheme by testing the model '
            'solutions against the marking criteria. The test is '
            'valid if the model solutions obtain maximum marks in '
            'each exercise.'
        ),
    )
    validate_parser.set_defaults(func=partial(validate, markscheme))
    help_parser = sub_parsers.add_parser(
        'help', help='Print the markingpy help to console.'
    )
    
    def display_help(*_):
        parser.print_help()
        parser.exit()

    help_parser.set_defaults(func=display_help)
    parser.set_defaults(func=display_help)
    new_args = parser.parse_args(args)
    new_args.func(new_args)


def run_ms(markscheme, args):
    target = getattr(args, 'target', None)
    if target is not None:
        delattr(args, "target")
        markscheme.finder = finders.DirectoryFinder(target)
    #markscheme.update_config(vars(args))
    #markscheme.validate()
    for sub in markscheme.run():
        print(sub.reference, sub.percentage)



def summary(markscheme, args):
    print('Printing summary')
    markscheme.update_config(vars(args))
    subs = markscheme.get_db().fetch_all()
    percs = [sub[1] for sub in subs]
    mean = statistics.mean(percs)
    stdev = statistics.stdev(percs)
    print(
        f"Summary: Number of submissions = {len(subs)}, "
        f"Mean = {mean}%, Standard = {stdev:.4}%"
    )


def grades(markscheme, args):
    print('Printing grades')
    markscheme.update_config(vars(args))
    subs = markscheme.get_db().fetch_all()
    for sid, perc, _ in subs:
        print(f"{sid:60}: {perc}%")


def dump(markscheme, args):
    print('Dumping feedback')
    args = vars(args)
    path = Path(args.pop("path"))
    if path.exists() and not path.is_dir():
        raise ValueError('{path} is not a directory')

    path.mkdir(exist_ok=True)
    markscheme.update_config(args)
    for sub_id, _, fb in markscheme.get_db().fetch_all():
        (path / (sub_id + ".txt")).write_text(fb)


def validate(markscheme, args):
    print('Validating marking scheme')
    markscheme.validate()


def main():
    """
    Main command line runner.
    """
    try:
        run()
    except KeyboardInterrupt:
        print('Keyboard interrupt')
    except Exception as err:
        import traceback

        tb = '\n'.join(traceback.format_tb(err.__traceback__))
        print(f"{err.__class__.__name__}: {err}\n{tb}")


if __name__ == "__main__":
    main()
