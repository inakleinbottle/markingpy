import logging
import types
import typing
import inspect

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

    :param call_args: Arguments to use.
    :param call_kwargs: Keyword arguments to use.
    :param expects_error: Exception(s) to expect on execution.

        .. versionadded:: 0.2.0
    :param tolerance: Tolerance to allow in numerical equality testing.
        Defaults to None, which is inactive (equality must be exact).
        This option cannot be used with non-numerical output.

        .. versionadded:: 0.2.0

    """
    call_args: args
    call_kwargs: kwargs

    def __init__(self, call_args, call_kwargs, *,
                 expects_error=None, tolerance=None,
                 **kwargs):
        self.call_args = call_args
        self.call_kwargs = call_kwargs
        self.expects_error = expects_error
        self.tolerance = tolerance
        super().__init__(**kwargs)
        self.expected = self.get_expected()
        if (tolerance is not None
                and not isinstance(self.expected, numbers.Number)):
            raise TypeError('Near matches are not available for non-numeric '
                            'types')

    def get_expected(self):
        """
        Get the expected return to test
        :return:
        """
        return self.exercise.func(
            * self.call_args, ** self.call_kwargs
            )

    def create_test(self, other):
        return ExecutionContext()

    def get_success(self, ctx, test_output):
        if self.expects_error is not None:
            err = ctx.error
            if isinstance(err[1], self.expects_error):
                return True
            return False

        if test_output == self.expected:
            return True

        if self.tolerance is None:
            return False

        if not isinstance(test_output, numbers.Number):
            return False

        diff = abs(test_output - self.expected)
        return diff < self.tolerance

    def run(self, other):
        args_msg = str_format_args(self.call_args, self.call_kwargs)
        print(f'Testing with input: ({args_msg})')
        output = other(* self.call_args, ** self.call_kwargs)
        print(f'Expected: {self.expected}, got: {output}')
        return output


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
                    TimingCase(*call, self.get_target(call))
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

    def create_test(self, other):
        return ExecutionContext()

    def get_target(self, call: Call):
        return time_run(self.exercise.func, call.args, call.kwargs)

    def run(self, other):
        for args, kwargs, target in self.cases:
            print(f'Running: ({str_format_args(args, kwargs)})')
            runtime = time_run(other, args, kwargs)
            if runtime is None:
                raise ExecutionFailedError
            print(f'Target time: {target:5.5g}, run time: {runtime:5.5g}')

            if not runtime <= (1.0 + self.tolerance) * target:
                break
        else:
            return True
        return False


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

    def create_test(self, other):
        ctx = ExecutionContext()
        ctx.add_context(self.exercise.set_function(other))
        return ctx

    def run(self, other):
        return self.test_func()


# noinspection PyUnresolvedReferences
class MethodTest(CallTest):
    """
    Variant of :class:`CallTest` for instance methods.

    :param method: Name of method to test.
    :param inst_args: Arguments to instantiate the object.
    :param inst_kwargs: Keyword arguments to instantiate the object
    """
    inst_args: args
    inst_kwargs: kwargs

    def __init__(
        self,
        method,
        call_args=None,
        call_kwargs=None,
        inst_args=None,
        inst_kwargs=None,
        **kwargs,
    ):
        self.method = method
        self.inst_args = inst_args
        self.inst_kwargs = inst_kwargs
        super().__init__(call_args, call_kwargs, **kwargs)

    def get_expected(self):
        inst = self.exercise(*self.inst_args, **self.inst_kwargs)
        func = getattr(inst, self.method)
        return func(*self.call_args, **self.call_kwargs)

    def run(self, other):
        instance = other(* self.inst_args, ** self.inst_kwargs)
        func = getattr(instance, self.method)
        return super().run(func)


# noinspection PyUnresolvedReferences
class MethodTimingTest(TimingTest):
    """
    Variant of :class:`TimingTest` for instance methods.

    :param method: Name of method to test.
    :param inst_args: Arguments to instantiate the object.
    :param inst_kwargs: Keyword arguments to instantiate the object
    """
    inst_args: args
    inst_kwargs: kwargs

    def __init__(
        self, method, cases, tolerance, inst_args, inst_kwargs, **kwargs
    ):
        self.method = method
        self.inst_args = inst_args
        self.inst_kwargs = inst_kwargs
        super().__init__(cases, tolerance, **kwargs)

    def get_target(self, call: Call):
        inst = self.exercise(*self.inst_args, **self.inst_kwargs)
        func = getattr(inst, self.method)
        return time_run(func, call.args, call.kwargs)

    def run(self, other):
        instance = other(* self.inst_args, ** self.inst_kwargs)
        func = getattr(instance, self.method)
        return super().run(func)


SuccessCriterion = namedtuple('SuccessCriterion',
                              ['name', 'descr', 'marks', 'criterion'])


class InteractionTest(BaseTest):
    """
    Test interaction with some object.
    """

    def __init__(self, cls, inst_call, **kwargs):
        self.cls = cls
        self.inst_call = inst_call
        self.instance = None
        self.success_criteria = []
        super().__init__(**kwargs)

    def create_proxy_ns(
            self,
            ns: typing.Dict[str, typing.Any]
        ):

        def getter(self_, name):
            if name.startswith('_'):
                raise AttributeError(
                    f'{self_.__class__.__name__} has no attribute {name}'
                )
            return getattr(self.instance, name)

        def setter(self_, name, val):
            if name.startswith('_'):
                raise TypeError(f'Cannot set attribute {name}')
            return setattr(self.instance, name, val)

        ns['__getattr__'] = getter
        ns['__setattr__'] = setter

    def create_instance_proxy(self):
        self.instance = self.cls(*self.inst_call.args,
                                 **self.inst_call.kwargs)
        proxy_cls = types.new_class('Proxy', (),
                                    exec_body=self.create_proxy_ns)
        return proxy_cls()

    def success_criterion(self, name=None, descr=None, marks=None):

        if inspect.isfunction(name):
            fn = name
            name = None
        else:
            fn = None

        def deco(func):
            self.success_criteria.append(
                SuccessCriterion(name, descr, marks, func)
            )
            return func

        if fn:
            return deco(fn)
        else:
            return deco

    def create_test(self, other):
        return ExecutionContext()

    def get_success(self, ctx, test_output):
        crt = self.success_criteria
        return (ctx.ran_successfully
                and all(c.criterion(test_output) for c in crt))

    def run(self, other):
        return other(self.create_instance_proxy())