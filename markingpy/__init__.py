"""The MarkingPy package"""


from os.path import expanduser, join as pathjoin

from .grader import Grader
from .exercise import Exercise

__all__ = ['Grader', 'CONFIG_PATHS', 'Exercise']

CONFIG_PATHS = [expanduser(pathjoin('~', '.markingpy'))]
