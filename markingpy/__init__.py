"""The MarkingPy package"""

import logging

from .grader import Grader
from .exercise import exercise
from .markscheme import mark_scheme
from .cases import Test


logging.basicConfig(level=logging.INFO)


__all__ = ['Grader', 'mark_scheme', 'exercise',]





