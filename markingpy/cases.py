import inspect
import logging

from abc import ABC, abstractmethod
from collections import namedtuple, abc
from contextlib import redirect_stdout
from io import StringIO
from typing import Callable


from .utils import log_calls, time_run
from .execution import ExecutionContext
from .import magic

logger = logging.getLogger(__name__)
TestFeedback = namedtuple("TestFeedback", ("test", "mark", "feedback"))


# noinspection PyUnresolvedReferences
class BaseTest(magic.MagicBase):
    """
    Abstract base class for Test components.

    :param name: Name of the test. Defaults to the name of the class.
    :param descr: Short description to be displayed in feedback.
    :param marks: Marks to award for this component, default=0.
    """
    name: common(str)
    descr: common(str)
    marks: common(None)
    __enforced = ["create_test", "run"]
    indent = " " * 4

    def __init__(self, *, name=None, descr=None, marks=0, exercise=None):
        self.exercise = exercise
        self.name = name
        self.descr = descr
        self.marks = marks

    def get_name(self):
        return self.__class__.__name__

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

    def create_test(self, other):
        """
        Create the execution context  for this test.

        :param other:
        :return: ExecutionContext instance
        """

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
        return "\n.".join(self.indent + line for line in str(err[1]).splitlines())

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


# noinspection PyUnresolvedReferences
class CallTest(BaseTest):
    call_args: args
    call_kwargs: kwargs

    def __init__(self, call_args, call_kwargs, *args, **kwargs):
        self.call_args = call_args
        self.call_kwargs = call_kwargs
        super().__init__(*args, **kwargs)
        self.expected = self.exercise.func(*self.call_args, **self.call_kwargs)

    @log_calls
    def create_test(self, other):
        return ExecutionContext()

    def run(self, other):
        output = other(*self.call_args, **self.call_kwargs)
        return output == self.expected


Call = namedtuple("Call", ("args", "kwargs"))
TimingCase = namedtuple("TimingCase", ("call_args", "call_kwargs", "target"))


class TimingTest(BaseTest):
    """

    """

    def __init__(self, cases, tolerance, **kwargs):
        if isinstance(cases, dict):
            # cases from dict - preset targets
            cases = [
                TimingCase(*call, target)
                for call, target in cases.items()
                if isinstance(call, Call)
                if target > 0
            ]
        elif isinstance(cases, abc.Iterable):
            # cases from iterable, each item is a separate call
            if not all(isinstance(case, TimingCase) for case in cases):
                cases = [
                    TimingCase(*call, time_run(self.exercise.func, *call))
                    for call in cases
                    if isinstance(call, Call)
                ]
        else:
            cases = None
        if not cases:
            raise ValueError("Cases not correctly defined.")

        self.cases = cases
        self.tolerance = tolerance
        super().__init__(**kwargs)

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
        self.test_func = test_func
        super().__init__(*args, **kwargs)

    def get_name(self):
        return self.test_func.__name__

    @log_calls
    def create_test(self, other):
        ctx = ExecutionContext()
        ctx.add_context(self.exercise.set_function(other))
        return ctx

    def run(self, other):
        return self.test_func()




# noinspection PyUnresolvedReferences
class MethodTest(BaseTest):
    call_params: args
    call_kwparams: kwargs
    inst_args: args
    inst_kwargs: kwargs

    def __init__(
        self,
        method,
        call_params=None,
        call_kwparams=None,
        inst_args=None,
        inst_kwargs=None,
        *args,
        **kwargs,
    ):
        self.method = method
        self.call_args = call_params
        self.call_kwargs = call_kwparams
        self.inst_args = inst_args
        self.inst_kwargs = inst_kwargs
        super().__init__(*args, **kwargs)

    def create_test(self, other):
        return ExecutionContext()

    def run(self, other):
        instance = other(* self.inst_args, ** self.inst_kwargs)
        func = getattr(instance, self.method)
        output = func(* self.call_args, ** self.call_kwargs)
        return output == self.expected




# noinspection PyUnresolvedReferences
class MethodTimingTest(BaseTest):
    inst_args: args
    inst_kwargs: kwargs

    def __init__(self, method, cases, tolerance, inst_args, inst_kwargs, **kwargs):
        if isinstance(cases, dict):
            # cases from dict - preset targets
            cases = [
                TimingCase(*call, target)
                for call, target in cases.items()
                if isinstance(call, Call)
                if target > 0
            ]
        elif isinstance(cases, abc.Iterable):
            # cases from iterable, each item is a separate call
            if not all(isinstance(case, TimingCase) for case in cases):
                cases = [
                    TimingCase(*call, time_run(self.exercise.func, *call))
                    for call in cases
                    if isinstance(call, Call)
                ]
        else:
            cases = None
        if not cases:
            raise ValueError("Cases not correctly defined.")

        self.cases = cases
        self.method = method
        self.tolerance = tolerance
        self.inst_args = inst_args
        self.inst_kwargs = inst_kwargs
        super().__init__(**kwargs)

    def create_test(self, other):
        return ExecutionContext()

    def run(self, other):
        instance = other(* self.inst_args, ** self.inst_kwargs)
        func = getattr(instance, self.method)
        success = True
        for args, kwargs, target in self.cases:
            runtime = time_run(func, args, kwargs)
            if runtime is None:
                raise ExecutionFailedError

            success ^= runtime <= (1.0 + self.tolerance) * target
        return success
