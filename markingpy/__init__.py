"""The MarkingPy package"""

import logging
from os.path import expanduser, join as pathjoin


from .grader import Grader

from .exercise import Exercise, mark_scheme

logging.basicConfig(level=logging.INFO)





__all__ = ['Grader', 'CONFIG_PATHS', 'Exercise', 'mark_scheme']

CONFIG_PATHS = [expanduser(pathjoin('~', '.markingpy')),
                '.markingpy']
