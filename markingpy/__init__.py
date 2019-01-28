#      Markingpy automatic grading tool for Python code.
#      Copyright (C) 2019 Sam Morley
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""The MarkingPy package"""


import logging

from .import exercises
from .import cases
from .import compiler
from .import config
from .import execution
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
from .execution import *

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
    execution.__all__ +
    ['utils']
)
