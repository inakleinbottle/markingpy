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
import logging
import os

from configparser import ConfigParser
from pkgutil import get_data
from pathlib import Path

__all__ = ['CONFIG_PATHS', 'LOGGING_LEVELS', 'GLOBAL_CONF', 'logger']
CONFIG_PATHS = [Path.home() / ".markingpy"]
LOGGING_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def load_config() -> ConfigParser:
    """
    Configuration file loader for markingpy.
    """
    parser = ConfigParser()
    parser.read_string(get_data("markingpy", "data/markingpy.conf").decode())
    parser.read(CONFIG_PATHS)
    DEBUG_FLAG = os.getenv("MARKINGPY_DEBUG", None)
    if DEBUG_FLAG:
        parser["logging"]["level"] = "debug"
    return parser


GLOBAL_CONF = load_config()
logging.basicConfig(level=LOGGING_LEVELS[GLOBAL_CONF["logging"]["level"]])
logger = logging.getLogger(__name__)
