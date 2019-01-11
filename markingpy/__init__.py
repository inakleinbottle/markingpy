"""The MarkingPy package"""

import logging

from .config import GLOBAL_CONF, LOGGING_LEVELS
from .grader import Grader
from .exercise import exercise, Exercise
from .markscheme import mark_scheme
from .cases import Test

logging.basicConfig(level=LOGGING_LEVELS[GLOBAL_CONF["logging"]["level"]])

__all__ = ["Grader", "mark_scheme", "exercise", "Exercise", "Test"]
