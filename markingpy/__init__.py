from os.path import expanduser, join as pathjoin

from .grader import Grader


__all__ = ['Grader', 'CONFIG_PATHS']

CONFIG_PATHS = [expanduser(pathjoin('~', '.markingpy'))]

