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
"""Execution context for running tests"""
import sys
import logging
from io import StringIO
from contextlib import (
    redirect_stdout, redirect_stderr, contextmanager, ExitStack
)
from warnings import catch_warnings

logger = logging.getLogger(__name__)
__all__ = ['ExecutionContext']


class ExecutionContext:

    def __init__(self):
        self.ran_successfully = True
        self.contexts = []
        self.error = None
        self.warnings = None
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.set_up_actions = []
        self.clean_up_actions = []

    def exception_handler(self):
        self.ran_successfully = False
        self.error = sys.exc_info()

    def do_set_up(self):
        for action in self.set_up_actions:
            action()

    def do_clean_up(self):
        for action in self.clean_up_actions:
            action()

    def add_set_up(self, action):
        self.set_up_actions.append(action)

    def add_context(self, context_manager):
        self.contexts.append(context_manager)

    def add_clean_up(self, action):
        self.clean_up_actions.append(action)

    @contextmanager
    def catch(self):
        self.do_set_up()
        warned = None
        # noinspection PyBroadException
        try:
            with ExitStack() as stack:
                stack.enter_context(redirect_stdout(self.stdout))
                stack.enter_context(redirect_stderr(self.stderr))
                warned = stack.enter_context(catch_warnings(record=True))
                for ctx in self.contexts:
                    stack.enter_context(ctx)
                yield

        except KeyboardInterrupt:
            raise

        except Exception:
            self.exception_handler()
        finally:
            self.warnings = warned
            self.do_clean_up()
