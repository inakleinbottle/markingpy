"""The MarkingPy package"""

import logging
from os.path import expanduser, join as pathjoin
from configparser import ConfigParser
from pkgutil import get_data

logging.basicConfig(level=logging.INFO)

CONFIG_PATHS = [expanduser(pathjoin('~', '.markingpy'))]


def load_config():
    """
    Configuration file loader for markingpy.
    """
    parser = ConfigParser()
    parser.read_string(get_data('markingpy', 'data/markingpy.conf').decode())
    parser.read(CONFIG_PATHS)
    return parser


GLOBAL_CONF = load_config()

__all__ = ['Grader', 'GLOBAL_CONF', 'mark_scheme', 'exercise']

from .grader import Grader
from .exercise import exercise
from .markscheme import mark_scheme





