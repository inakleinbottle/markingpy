import logging

from collections import namedtuple, abc
from contextlib import redirect_stdout
from io import StringIO
from typing import Callable


from .utils import log_calls, time_run, str_format_args
from .execution import ExecutionContext
from . import magic

logger = logging.getLogger(__name__)
TestFeedback = namedtuple("TestFeedback", ("test", "mark", "feedback"))
__all__ = [
    'BaseTest',
    'Test',
    'CallTest',
    'TimingTest',
    'TimingCase',
    'TestFeedback',
    'MethodTest',
    'MethodTimingTest',
    'Call',
]


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
        raise NotImplementedError

    def run(self, other):
        """
        Run the test.
        """
        raise NotImplementedError

    def get_success(self, ctx, test_output):
        """
        Examine result and determine whether a test was successful.

        :param ctx:
        :param test_output:
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
            for line in str(warning.message).strip().splitlines()
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

        stdout = context.stdout.getvalue().strip()
        if stdout:
            feedback.append(self.format_stdout(stdout))

        err, warnings = context.error, context.warnings
        if err:
            feedback.append(self.format_error(err))
        if warnings:
            feedback.append(self.format_warnings(warnings))

        return TestFeedback(self, marks, "\n".join(feedback))


class ExecutionFailedError(Exception):
    pass


# noinspection PyUnresolvedReferences
class CallTest(BaseTest):
    """
    Test output of submission function against model solution function.

    Runs the submission function with the provided *calL_args* and
    *call_kwargs* and compares the output against the the model solution
    output.

    Keyword arguments are forwarded to the underlying :class:`BaseTest`
    instance.

    :param call_args:
    :param call_kwargs:

    """
    call_args: args
    call_kwargs: kwargs

    def __init__(self, call_args, call_kwargs, *args, **kwargs):
        self.call_args = call_args
        self.call_kwargs = call_kwargs
        super().__init__(*args, **kwargs)
        self.expected = self.exercise.func(
            * self.call_args, ** self.call_kwargs
            )

    @log_calls
    def create_test(self, other):
        return ExecutionContext()

    def run(self, other):
        args_msg = str_format_args(self.call_args, self.call_kwargs)
        print(f'Testing with input: ({args_msg})')
        output = other(* self.call_args, ** self.call_kwargs)
        print(f'Expected: {self.expected}, got: {output}')
        return output == self.expected


Call = namedtuple("Call", ("args", "kwargs"))
TimingCase = namedtuple("TimingCase", ("call_args", "call_kwargs", "target"))


class TimingTest(BaseTest):
    """
    Test relative efficiency of test function using timing cases.

    Run a sequence of timed calls to the submission function and compare the
    running time to the model solution function or manually entered target
    time. The test is passed if every execution time does not exceed the
    corresponding target time plus some tolerance.

    Keyword arguments are forwarded to the underlying :class:`BaseTest`
    instance.

    :param cases: Calls to test timing of submission function. Each should
        be an instance of the TimingCase named tuple, containing the *args*,
        *kwargs*, and *target* time.
    :param tolerance:
        Percentage tolerance for which a submission run time can exceed the
        target time. This is applied to the target time in at test time using
        the formula::

            real_target = (1.0 + tolerance) * target
    """

    def __init__(self, cases, tolerance, **kwargs):
        super().__init__(**kwargs)
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

        logger.info(
                'Adding timing test with cases:'
                f'\n{", ".join(str(c) for c in cases)}\n)'
                )

        self.cases = cases
        self.tolerance = tolerance


    @log_calls
    def create_test(self, other):
        return ExecutionContext()

    def run(self, other):
        success = True
        for args, kwargs, target in self.cases:
            print(f'Running: ({str_format_args(args, kwargs)})')
            runtime = time_run(other, args, kwargs)
            print(f'Target time: {target:5.5g}, run time: {runtime:5.5g}')
            if runtime is None:
                raise ExecutionFailedError

            success ^= runtime <= (1.0 + self.tolerance) * target
        return success


class Test(BaseTest):
    """
    Custom test class based on a user defined function written in the
    marking scheme file.

    This class provides a wrapper around a user defined testing function to
    set up the execution context and format the results passed back to the
    grader. This class should be instantiated by applying the
    :func:`~markingpy.Exercise.test` decorator.

    The testing function can contain arbitrary Python code and use the
    parent exercise name to refer to the submission function. Feedback can
    be provided to the submission using the standard ``print`` function. The
    testing function should return ``True`` on a successful test and
    ``False`` on a failed test.

    Uncaught exceptions that are raised within the testing function will be
    propagated to the execution context, which will terminate the test. This
    will usually result in a test failure.

    Keyword arguments are forwarded to the underlying :class:`BaseTest`
    instance.

    :param test_func: Testing function.
    """

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

    def __init__(
        self, method, cases, tolerance, inst_args, inst_kwargs, **kwargs
    ):
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
