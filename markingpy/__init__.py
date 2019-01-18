"""The MarkingPy package"""

import logging

from .import exercises
from .import cases
from .import compiler
from .import config
from .import finders
from .import grader
from .import linters
from .import markscheme
from .import submission
from .import utils

from .config import *
from .grader import *
from .exercises import *
from .markscheme import *
from .cases import *
from .submission import *
from .linters import *
from .finders import *
from .compiler import *

logging.basicConfig(level=LOGGING_LEVELS[GLOBAL_CONF["logging"]["level"]])
__all__ = (
    cases.__all__ +
    config.__all__ +
    compiler.__all__ +
    exercises.__all__ +
    finders.__all__ +
    grader.__all__ +
    linters.__all__ +
    markscheme.__all__ +
    submission.__all__ +
    ['utils']
)
