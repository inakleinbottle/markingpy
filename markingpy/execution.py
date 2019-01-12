"""Execution context for running tests"""
import sys
import logging
from io import StringIO
from contextlib import (
    redirect_stdout,
    redirect_stderr,
    contextmanager,
    ExitStack,
)
from warnings import catch_warnings

logger = logging.getLogger(__name__)


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
