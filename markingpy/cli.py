"""Command line interface for MarkingPy."""

import sys
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

    parser = ArgumentParser()

    args = parser.parse_args()


    return 0


def is_markscheme(path):
    is_ms = False
    if not isinstance(path, Path):
        return is_ms
    if not path.name.endswith('.py'):
        return is_ms
    if not path.exists():
        return is_ms
    text = path.read_text()
    if 'import markingpy' in text or 'from markingpy import' in text:
        is_ms = True
    return is_ms


class MarkschemeCommands:

    @staticmethod
    def run(markscheme, cli_args):
        parser = ArgumentParser()

        parser.add_argument('--style-formula', type=str)
        parser.add_argument('--style-marks', type=int)
        parser.add_argument(
            '--score-style',
            choices=['real', 'percentage', 'marks/total', 'all'],
            default='all'
        )
        parser.add_argument('--submission-path', type=str)
        parser.add_argument('--marks-db', type=str)
        markscheme.update_config(vars(parser.parse_args(cli_args)))

        grader = Grader(markscheme)
        with grader:
            grader.grade_submissions()

    @staticmethod
    def grades(markscheme, cli_args):
        parser = ArgumentParser()
        parser.add_argument('--marks-db', type=str)
        markscheme.update_config(vars(parser.parse_args(cli_args)))

        subs = markscheme.get_db().fetch_all()
        for sid, perc, _ in subs:
            print(f"{sid:60}: {perc}%")

    @staticmethod
    def summary(markscheme, cli_args):
        import statistics
        parser = ArgumentParser()
        parser.add_argument('--marks-db', type=str)
        markscheme.update_config(vars(parser.parse_args(cli_args)))

        subs = markscheme.get_db().fetch_all()
        percs = [sub[1] for sub in subs]
        mean = statistics.mean(percs)
        stdev = statistics.stdev(percs)
        print(f'Summary: Number of submissions = {len(subs)}, Mean = {mean}%, Standard = {stdev:.4}%')

    @staticmethod
    def dump(markscheme, cli_args):
        parser = ArgumentParser()
        parser.add_argument('--marks-db', type=str)
        parser.add_argument('path', default='.', nargs='?')
        args = vars(parser.parse_args(cli_args))
        path = Path(args.pop('path'))

        markscheme.update_config(args)
        for sub_id, _, fb in markscheme.get_db().fetch_all():
            (path / (sub_id + '.txt')).write_text(fb)


def main():
    """
    Main command line runner.
    """
    try:
        path = Path(sys.argv[1])
    except IndexError:
        return run()

    args = sys.argv[3:]

    try:
        cmd = sys.argv[2]
    except IndexError:
        cmd = 'run'
        args = []

    if not is_markscheme(path):
        return run()

    markscheme = import_markscheme(path)
    try:
        fn = getattr(MarkschemeCommands, cmd)
    except AttributeError:
        args = [cmd] + args
        fn = MarkschemeCommands.run
    fn(markscheme, args)













if __name__ == "__main__":
    main()
