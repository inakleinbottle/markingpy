"""Command line interface for MarkingPy."""

import sys
from argparse import ArgumentParser
from os.path import exists as pathexists
from pathlib import Path

from .config import GLOBAL_CONF
from .markscheme import NotAMarkSchemeError


class CLIError(Exception):
    pass





def run():
    """
    Build the argument parser and run the grader.
    """
    config = GLOBAL_CONF

    parser = ArgumentParser()
    parser.add_argument(
        "scheme", default=None, help="The marking scheme for this submission"
    )
    # parser.add_argument('submissions', default=None,
    #                    help='The directory containing submission files')
    parser.add_argument(
        "-c", "--csv", default=None, help="Save submission grades to csv"
    )
    parser.add_argument(
        "-m",
        "--mail",
        action="store_true",
        help="Send results to submitter by email",
    )
    parser.add_argument(
        "-o", "--out", default=None, help="Directory to store reports"
    )
    args = parser.parse_args()

    if args.scheme is not None and not pathexists(args.scheme):
        raise CLIError("Marking scheme %s cannot be found" % args.scheme)
    elif args.scheme is None:
        path = config["grader"]["scheme"]
        if not pathexists(path):
            raise CLIError("Marking scheme %s cannot be found" % path)
        args.scheme = path

    if args.out or args.csv:
        args.print = False
    else:
        args.print = True

    return 0

def main_cli():
    pass


def main():
    from .markscheme import import_markscheme
    from .grader import Grader
    """
    Main command line runner.
    """

    try:
        path = Path(sys.argv[1])
        cmd, markscheme = import_markscheme(path)

        if cmd == 'run':
            grader = Grader(markscheme)

            with grader:
                grader.grade_submissions()
        elif cmd == 'grades':
            subs = markscheme.get_db().fetch_all()
            for sid, perc, _ in subs:
                print(f"{sid:60}: {perc}%")
    except NotAMarkSchemeError:
        main_cli() # No marking scheme file provided,
    except IndexError:
        main_cli()



if __name__ == "__main__":
    main()
