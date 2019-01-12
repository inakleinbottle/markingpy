import logging

from abc import ABC, abstractmethod
from collections import namedtuple
from collections.abc import Iterable, Mapping
from contextlib import redirect_stdout
from io import StringIO
from typing import Callable


from .utils import log_calls, time_run
from .execution import ExecutionContext

logger = logging.getLogger(__name__)


TestFeedback = namedtuple("TestFeedback", ("test", "mark", "feedback"))


class BaseTest(ABC):
    """
    Abstract base class for Test components.

    :param name: Name of the test. Defaults to the name of the class.
    :param descr: Short description to be displayed in feedback.
    :param marks: Marks to award for this component, default=0.
    """

    _common_properties = ["name", "descr", "marks"]
    indent = " " * 4

    def __init__(self, *, name=None, descr=None, marks=0, exercise=None):
        self.exercise = exercise
        self.name = name
        self.descr = descr
        self.marks = marks

    def get_name(self):
        return self.__class__.__name__

    def __getattribute__(self, item):
        getter = object.__getattribute__
        common_properties = getter(self, "_common_properties")
        try:
            attr = getter(self, item)
        except AttributeError:
            if item in common_properties:
                attr = None
            else:
                raise
        if (
            item in common_properties
            and attr is None
            and hasattr(self, "get_" + item)
        ):
            attr = getter(self, "get_" + item)()
            setattr(self, item, attr)
        return attr

    def __str__(self):
        rv = self.name.replace("_", " ")
        if self.descr:
            rv += "\n" + self.descr
        return rv

    def __call__(self, other):
        """
        Run the test.

        :param other: Function to test.
        :return:
        """
        submission_stdout = StringIO()

        def wrapped(*args, **kwargs):
            with redirect_stdout(submission_stdout):
                rv = other(*args, **kwargs)
            return rv

        test_output = None
        ctx = self.create_test(wrapped)
        with ctx.catch():
            test_output = self.run(wrapped)
        return self.format_feedback(ctx, test_output)

    @abstractmethod
    def create_test(self, other):
        """
        Create the execution context  for this test.

        :param other:
        :return: ExecutionContext instance
        """

    @abstractmethod
    def run(self, other):
        """
        Run the test.
        """

    def get_success(self, ctx, test_output):
        """
        Examine result and determine whether a test was successful.

        :param result:
        :return:
        """
        return ctx.ran_successfully and test_output

    def get_marks(self, ctx, test_output, success):
        return self.marks if success else 0

    def format_error(self, err):
        return "\n.".join(
            self.indent + line for line in str(err[1]).splitlines()
        )

    def format_warnings(self, warnings):
        return "\n".join(
            self.indent + line.strip()
            for warning in warnings
            for line in str(warning).strip().splitlines()
        )

    def format_stdout(self, stdout):
        return "\n".join(self.indent + line for line in stdout.splitlines())

    def format_feedback(self, context: ExecutionContext, test_output):
        """
        Collect information and format feedback.

        :param test_output:
        :param context:
        :return: TestFeedback named tuple (test, mark, feedback
        """
        success = self.get_success(context, test_output)
        outcome = "Pass" if success else "Fail"
        marks = self.get_marks(context, test_output, success)
        msg = "Outcome: {}, Marks: {}"
        feedback = [str(self), msg.format(outcome, marks)]
        err, warnings = context.error, context.warnings
        if err:
            feedback.append(self.format_error(err))
        if warnings:
            feedback.append(self.format_warnings(warnings))

        stdout = context.stdout.getvalue().strip()
        if stdout:
            feedback.append(self.format_stdout(stdout))

        return TestFeedback(self, marks, "\n".join(feedback))


class ExecutionFailedError(Exception):
    pass


class CallTest(BaseTest):
    def __init__(self, call_args, call_kwargs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.call_args = call_args
        self.call_kwargs = call_kwargs
        self.expected = self.exercise(*self.call_args, **self.call_kwargs)

    @property
    def call_args(self):
        return self._call_args

    @call_args.setter
    def call_args(self, call_args):
        if call_args is None:
            self._call_args = ()
        elif isinstance(call_args, str):
            self._call_args = (call_args,)
        elif isinstance(call_args, Iterable):
            self._call_args = tuple(call_args)
        else:
            self._call_args = (call_args,)

    @property
    def call_kwargs(self):
        return self._call_kwargs

    @call_kwargs.setter
    def call_kwargs(self, call_kwargs):
        if call_kwargs is None:
            self._call_kwargs = {}
        elif isinstance(call_kwargs, Mapping):
            self._call_kwargs = dict(call_kwargs)
        else:
            raise TypeError("Keyword arguments must be mapping type or None")

    @log_calls
    def create_test(self, other):
        return ExecutionContext()

    def run(self, other):
        output = other(*self.call_args, **self.call_kwargs)
        return output == self.expected


TimingCase = namedtuple("TimingCase", ("call_args", "call_kwargs", "target"))


class TimingTest(BaseTest):
    """

    """

    def __init__(self, cases, tolerance, **kwargs):
        super().__init__(**kwargs)
        self.cases = cases
        self.tolerance = tolerance

    @log_calls
    def create_test(self, other):
        return ExecutionContext()

    def run(self, other):
        success = True
        for args, kwargs, target in self.cases:
            runtime = time_run(other, args, kwargs)
            if runtime is None:
                raise ExecutionFailedError
            success ^= runtime <= (1.0 + self.tolerance) * target
        return success


class Test(BaseTest):
    def __init__(self, test_func: Callable[..., bool], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_func = test_func

    def get_name(self):
        return self.test_func.__name__

    @log_calls
    def create_test(self, other):
        ctx = ExecutionContext()
        ctx.add_context(self.exercise.set_function(other))
        return ctx

    def run(self, other):
        return self.test_func()
