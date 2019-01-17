"""The MarkingPy package"""

import logging

from .config import GLOBAL_CONF, LOGGING_LEVELS
from .grader import Grader
from .exercise import exercise, Exercise, FunctionExercise, ClassExercise
from .markscheme import mark_scheme
from .cases import Test, CallTest, TimingTest, MethodTest, MethodTimingTest

logging.basicConfig(level=LOGGING_LEVELS[GLOBAL_CONF["logging"]["level"]])
__all__ = [
    "Grader",
    "mark_scheme",
    "exercise",
    "Exercise",
    "Test",
    "FunctionExercise",
    "ClassExercise",
    "CallTest",
    "TimingTest",
    "MethodTest",
    "MethodTimingTest",
]
