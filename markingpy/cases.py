
import logging

from abc import ABC, abstractmethod
from collections import namedtuple
from collections.abc import Iterable, Mapping
from contextlib import redirect_stdout
from io import StringIO
from types import new_class
from typing import Callable, Any
from unittest import TestCase, TestResult

from .utils import log_calls, time_run

logger = logging.getLogger(__name__)


TestFeedback = namedtuple('TestFeedback', ('test', 'mark', 'feedback'))


INDENT = ' '*4


class BaseTest(ABC):
    """
    Abstract base class for Test components.

    :param name: Name of the test. Defaults to the name of the class.
    :param descr: Short description to be displayed in feedback.
    :param marks: Marks to award for this component, default=0.
    """

    _common_properties = ['name', 'descr', 'marks']
    result_class = TestResult
    test_class = TestCase

    def __init__(self, *, name=None, descr=None, marks=0, exercise=None):
        self.exercise = exercise
        self.name = name
        self.descr = descr
        self.marks = marks
        
    def get_name(self):
        return self.__class__.__name__

    def __getattribute__(self, item):
        getter = object.__getattribute__
        common_properties = getter(self, '_common_properties')
        try:
            attr = getter(self, item)
        except AttributeError:
            if item in common_properties:
                attr = None
            else:
                raise
        if (item in common_properties
            and attr is None
            and hasattr(self, 'get_' + item)):
                attr = getter(self, 'get_' + item)()
                setattr(self, item, attr)
        return attr

    def __str__(self):
        rv = self.name.replace('_', ' ')
        if self.descr:
            rv += '\n' + self.descr
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

        test = self.create_test(wrapped)
        result = self.result_class()
        test_stdout = StringIO()
        with redirect_stdout(test_stdout):
            test.run(result)
        return self.format_feedback(result, test_stdout)

    @abstractmethod
    def create_test(self, other):
        """
        Create the unittest TestCase instance for this test.

        :param other:
        :return: unittest.TestCase instance
        """

    def get_success(self, result):
        """
        Examine result and determine whether a test was successful.

        :param result:
        :return:
        """
        return result.wasSuccessful()

    def format_feedback(self, result, stdout):
        """
        Collect information and format feedback.

        :param result:
        :param stdout:
        :return: TestFeedback named tuple (test, mark, feedback
        """
        success = self.get_success(result)
        outcome = 'Pass' if success else 'Fail'
        marks = self.marks if success else 0
        msg = 'Outcome: {}, Marks: {}'
        feedback = [str(self), msg.format(outcome, marks)]
        feedback.extend(INDENT + line for err in result.errors
                        for line in err[1].strip().splitlines())
        feedback.extend(INDENT + line.strip()
                        for line in stdout.getvalue().strip().splitlines())
        return TestFeedback(self, marks, '\n'.join(feedback))


class CallTest(BaseTest):

    def __init__(self, call_args, call_kwargs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.call_args = call_args
        self.call_kwargs = call_kwargs

    @property
    def call_args(self):
        return self._call_args

    @call_args.setter
    def call_args(self, call_args):
        if call_args is None:
            self._call_args = ()
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
            raise TypeError('Keyword arguments must be mapping type or None')

    @log_calls
    def create_test(self, other):
        call_args, call_kwargs = self.call_args, self.call_kwargs
        equal_test = self.exercise(*call_args, **call_kwargs)

        def tester(tester_self):
            tester_self.assertEqual(equal_test,
                                    other(*call_args,
                                          **call_kwargs))
        cls = new_class(self.name, (self.test_class,))
        cls.runTest = tester
        return cls()


TimingCase = namedtuple('TimingCase', ('call_args', 'call_kwargs', 'target'))


class TimingTest(BaseTest):
    """

    """

    def __init__(self, cases, tolerance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = cases
        self.tolerance = tolerance

    @log_calls
    def create_test(self, other):
        tolerance = self.tolerance
        cases = self.cases

        def tester(tester_self):
            for args, kwargs, target in cases:
                runtime = time_run(other, args, kwargs)
                if runtime is None:
                    tester_self.fail(msg='Execution failed')
                tester_self.assertLessEqual(runtime, (1.0 + tolerance)*target)
        cls = new_class(self.name, (self.test_class,))
        cls.runTest = tester
        return cls()


class Test(BaseTest):

    def __init__(self, test_func: Callable[..., bool], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_func = test_func

    def get_name(self):
        return self.test_func.__name__

    @log_calls
    def create_test(self, other):
        test_func = self.test_func
        exercise = self.exercise

        def tester(tester_self):
            with exercise.set_function(other):
                output = test_func()
                tester_self.assertTrue(output)
        cls = new_class(self.name, (self.test_class,))
        cls.runTest = tester
        return cls()
