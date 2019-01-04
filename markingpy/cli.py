"""Command line interface for MarkingPy."""

import sys
from argparse import ArgumentParser
from os.path import exists as pathexists

from markingpy import Grader, GLOBAL_CONF


class CLIError(Exception):
    """
    Custom exception for command line Errors.
    """

    def __init__(self, msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg = msg





def run():
    """
    Build the argument parser and run the grader.
    """
    config = GLOBAL_CONF

    parser = ArgumentParser()
    parser.add_argument('submissions', default=None,
                        help='The directory containing submission files')
    parser.add_argument('scheme', default=None,
                        help='The marking scheme for this submission')
    parser.add_argument('-c', '--csv', default=None,
                        help='Save submission grades to csv')
    parser.add_argument('-m', '--mail', action='store_true',
                        help='Send results to submitter by email')
    parser.add_argument('-o', '--out', default=None,
                        help='Directory to store reports')
    args = parser.parse_args()

    if args.submissions is not None and not pathexists(args.submissions):
        raise CLIError('Submissions directory %s cannot be found'
                       % args.submissions)
    elif args.submissions is None:
        path = config['grader']['submissions']
        if not pathexists(path):
            raise CLIError('Submissions directory %s cannot be found'
                           % path)
        args.submissions = path

    if args.scheme is not None and not pathexists(args.scheme):
        raise CLIError('Marking scheme %s cannot be found' % args.scheme)
    elif args.scheme is None:
        path = config['grader']['scheme']
        if not pathexists(path):
            raise CLIError('Marking scheme %s cannot be found' % path)
        args.scheme = path
        
    if args.out or args.csv:
        args.print = False
    else:
        args.print = True

    with Grader(args.submissions, args.scheme) as grader:
        grader.grade_submissions(**vars(args))

    return 0


def main():
    """
    Main command line runner.
    """

    try:
        exit_code = run()
    except CLIError as e:
        print(e.msg)
        exit_code = 1
    except Exception as e:
        exit_code = 1
        raise
        

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
