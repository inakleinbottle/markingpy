"""Command line interface for MarkingPy."""

import sys
import statistics
from argparse import ArgumentParser
from pathlib import Path

from .config import GLOBAL_CONF
from .markscheme import import_markscheme
from .grader import Grader


class CLIError(Exception):
    pass


def run():
    """
    General markingpy cli
    """
    config = GLOBAL_CONF
    parser = ArgumentParser(
        description=(
            "Markingpy grading tool."
        )
    )
    args = parser.parse_args()
    return 0




class MarkschemeCommands:

    @staticmethod
    def run(markscheme, cli_args):
        parser = ArgumentParser(
            usage=f'markingpy {sys.argv[1]} run [OPTIONS]',
            description=(
                "Run the markingpy grader using the marking scheme "
                f"{sys.argv[1]}. The grader will use the settings "
                f"defined in {sys.argv[1]} along with any default "
                "values (set in .markingpy if this exists) or options passed "
                "to this command."
            )
        )

        parser.add_argument(
            "--style-formula",
            type=str,
            help="Formula used to generate a score from the linter report."
        )
        parser.add_argument(
            "--style-marks",
            type=int,
            help="Number of marks available for coding style."
        )
        parser.add_argument(
            "--score-style",
            help="Formatting style for marks to be displayed in feedback."
        )
        parser.add_argument(
            "--submission-path",
            type=str,
            help="Path to submissions."
        )
        parser.add_argument(
            "--marks-db",
            type=str,
            help="Path to database to store submission results and feedback."
        )
        parser.add_argument(
            "--marks",
            type=int,
            help=(
                "Total marks available for this coursework." 
                " This option is only used for validation."
            )
        )
        markscheme.update_config(vars(parser.parse_args(cli_args)))
        markscheme.validate()
        grader = Grader(markscheme)
        with grader:
            grader.grade_submissions()

    @staticmethod
    def grades(markscheme, cli_args):
        parser = ArgumentParser(
            usage=f'markingpy {sys.argv[1]} grades [OPTIONS]',
            description=(
                "Print the grades obtained in the last run of the grader"
                "with this marking scheme. This will load the results in"
                "the default database, the database specified in "
                f"{sys.argv[1]} or the database specified in the options for "
                "this command."
            )
        )
        parser.add_argument(
            "--marks-db",
            type=str,
            help="Path to database to store submission results and feedback."
        )
        markscheme.update_config(vars(parser.parse_args(cli_args)))
        subs = markscheme.get_db().fetch_all()
        for sid, perc, _ in subs:
            print(f"{sid:60}: {perc}%")

    @staticmethod
    def summary(markscheme, cli_args):
        parser = ArgumentParser(
            usage=f'markingpy {sys.argv[1]} summary [OPTIONS]',
            description=(
                "Print a summary of grades obtained in the last run of the "
                "grader with this marking scheme. This will load the results "
                "in the default database, the database specified in "
                f"{sys.argv[1]} or the database specified in the options for "
                "this command."
            )
        )
        parser.add_argument(
            "--marks-db",
            type=str,
            help="Path to database to store submission results and feedback."
        )
        markscheme.update_config(vars(parser.parse_args(cli_args)))
        subs = markscheme.get_db().fetch_all()
        percs = [sub[1] for sub in subs]
        mean = statistics.mean(percs)
        stdev = statistics.stdev(percs)
        print(
            f"Summary: Number of submissions = {len(subs)}, "
            f"Mean = {mean}%, Standard = {stdev:.4}%"
        )

    @staticmethod
    def dump(markscheme, cli_args):
        parser = ArgumentParser(
            usage=f'markingpy {sys.argv[1]} dump [OPTIONS] path',
            description=(
                "Dump the feedback obtained in the last run of the "
                "grader with this marking scheme into the directory 'path'. "
                "This will load the results in the default database, "
                f"the database specified in {sys.argv[1]} "
                "or the database specified in the options for "
                "this command."
            )
        )
        parser.add_argument(
            "--marks-db",
            type=str,
            help="Path to database to store submission results and feedback."
        )
        parser.add_argument(
            "path",
            default=".",
            nargs="?",
            help="Directory to populate with feedback."
        )
        args = vars(parser.parse_args(cli_args))
        path = Path(args.pop("path"))
        if path.exists() and not path.is_dir():
            raise ValueError('{path} is not a directory')
        path.mkdir(exists_ok=True)
        markscheme.update_config(args)
        for sub_id, _, fb in markscheme.get_db().fetch_all():
            (path / (sub_id + ".txt")).write_text(fb)

    @staticmethod
    def validate(markscheme, cli_args):
        markscheme.validate()


def main():
    """
    Main command line runner.
    """
    try:
        path = sys.argv[1]
    except IndexError:
        return run()

    args = sys.argv[3:]
    try:
        cmd = sys.argv[2]
    except IndexError:
        cmd = "run"
        args = []


    markscheme = import_markscheme(path)
    try:
        fn = getattr(MarkschemeCommands, cmd)
    except AttributeError:
        args = [cmd] + args
        fn = MarkschemeCommands.run
    fn(markscheme, args)


if __name__ == "__main__":
    main()
