"""The MarkingPy package"""

import logging
from os.path import expanduser, join as pathjoin

from .grader import Grader
from .exercise import Exercise

logging.basicConfig(level=logging.WARNING)




__all__ = ['Grader', 'CONFIG_PATHS', 'Exercise']

CONFIG_PATHS = [expanduser(pathjoin('~', '.markingpy')),
                '.markingpy']
