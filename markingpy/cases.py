
import logging

from abc import ABC, abstractmethod
from collections import namedtuple
from contextlib import redirect_stdout
from io import StringIO
from types import new_class
from unittest import TestCase, TestResult

from .utils import log_calls

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
        test = self.create_test(other)
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

    def __init__(self, call_args=None, call_kwargs=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.call_args = call_args if call_args else ()
        self.call_kwargs = call_kwargs if call_kwargs else {}

    @log_calls
    def create_test(self, other):
        call_args, call_kwargs = self.call_args, self.call_kwargs
        equal_test = self.exercise(*call_args, **call_kwargs)

        def tester(self):
            self.assertEqual(equal_test,
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
        from markingpy.utils import time_run
        tolerance = self.tolerance
        cases = self.cases

        def tester(self):
            for args, kwargs, target in cases:
                runtime = time_run(other, args, kwargs)
                if runtime is None:
                    self.fail(msg='Execution failed')
                self.assertLessEqual(runtime, (1.0 + tolerance)*target)
        cls = new_class(self.name, (self.test_class,))
        cls.runTest = tester
        return cls()


class Test(BaseTest):

    def __init__(self, test_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_func = test_func

    def get_name(self):
        return self.test_func.__name__

    @log_calls
    def create_test(self, other):
        test_func = self.test_func
        exercise = self.exercise

        def tester(self):
            with exercise.set_function(other):
                output = test_func()
            self.assertTrue(output)
        cls = new_class(self.name, (self.test_class,))
        cls.runTest = tester
        return cls()
