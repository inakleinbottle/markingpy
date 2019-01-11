"""Execution context for running tests"""
import sys
from io import StringIO
from contextlib import (
    redirect_stdout,
    redirect_stderr,
    contextmanager,
    ExitStack,
)
from warnings import catch_warnings


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

        try:
            with ExitStack() as stack:
                for ctx in self.contexts:
                    stack.enter_context(ctx)
                stack.enter_context(redirect_stdout(self.stdout))
                stack.enter_context(redirect_stderr(self.stderr))
                warned = stack.enter_context(catch_warnings(record=True))
                yield
        except KeyboardInterrupt:
            raise
        except Exception:
            self.ran_successfully = False
            self.error = sys.exc_info()
        finally:
            self.warnings = warned
            self.do_clean_up()
