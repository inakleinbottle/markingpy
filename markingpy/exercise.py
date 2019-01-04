"""
Exercise building utilities.
"""
import logging
from functools import wraps
from unittest import TestCase, TestResult
from unittest.mock import patch as patch
from collections import namedtuple
from types import new_class

from .utils import time_run

logger = logging.getLogger(__name__)

INDENT = ' '*4


def new_test_equal(model, call_args, call_kwargs):
    def tester(other):
        def test_method(self):
            self.assertEqual(other(*call_args, **call_kwargs),
                             model(*call_args, **call_kwargs))
        return test_method
    return tester


def new_test_true(func_name, test_func):
    def tester(other):
        def test_method(self):
            # with patch(test_func.__module__ + '.' + func_name, other):
            test_func.__globals__[func_name] = other
            output = test_func()
            if isinstance(output, bool):
                self.assertTrue(output)
            elif isinstance(output, tuple):
                outcome, feedback = output
                self.assertTrue(outcome)
        return test_method
    return tester


def new_timing_test(cases, tolerance):
    def tester(other):
        def test_method(self):
            for cs, target in cases:
                runtime = time_run(other, cs)
                if runtime is None:
                    self.fail(msg='Execution failed')
                self.assertLessEqual(runtime, (1.0 + tolerance)*target)

        return test_method
    return tester


class ExerciseError(Exception):
    pass


TestFeedback = namedtuple('TestFeedback', ('test', 'mark', 'feedback'))


class Test:

    def __init__(self, name, test_func, marks, descr=None, **kwargs):
        self.name = name
        self.marks = marks
        self.test_func = test_func
        self.descr = descr

    def create_test(self, other):
        """
        Create a unittest testcase for this test.

        :return: Unittest.TestCase.
        """
        test_case = new_class(self.name, (TestCase,))
        test_case.runTest = self.test_func(other)
        return test_case

    def format_feedback(self, result):
        """
        Format the feedback of the test.
        :param result:
        :return:
        """
        outcome, feedback = self.get_success(result)
        rv = [f'Ran {self.name}: {"Pass" if outcome else "Fail"}']
        if self.descr:
            rv.append(INDENT + self.descr)
        for fb in feedback:
            rv.append(INDENT + fb)
        return '\n'.join(rv)

    def get_success(self, result):
        """
        Determine whether the test was successful
        :param result:
        :return:
        """
        feedback = []
        success = result.wasSuccessful()
        if not success:
            for err in result.errors:
                feedback.append(err[1])
        return success, feedback

    def __call__(self, other):
        """
        Run test on specified other.
        :param other: Function to run test against.
        :return: Namedtuple containing Test, score, feedback
        """
        test = self.create_test(other)()
        result = TestResult()
        test.run(result)
        feedback = self.format_feedback(result)
        return TestFeedback(self, self.marks, feedback)


ExerciseFeedback = namedtuple('Feedback', ('marks', 'total_marks', 'feedback'))


class Exercise:

    def __init__(self, func, **args):
        wraps(func)(self)
        self.tests = []
        self.num_tests = 0
        self.func = func
        self.name = func.__name__

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    @property
    def total_marks(self):
        return sum(t.marks for t in self.tests)

    def add_test_call(self, call_params=None, call_kwparams=None, **args):
        """
        Add a call test to the exercise.

        Submission function is evaluated against the model solution, and is successful
        if both functions return the same value.

        :param call_params:
        :param call_kwparams:
        """
        call_params = call_params if call_params is not None else tuple()
        call_kwparams = call_kwparams if call_kwparams is not None else dict()
        self.num_tests += 1
        name = self.name + str(self.num_tests)
        test = Test(name, new_test_equal(self, call_params, call_kwparams), **args)
        self.tests.append(test)
        return test

    def timing_test(self, *cases, **args):
        """
        Test the timing of a submission against the model.

        :param cases:
        :param args:
        :return:
        """
        self.num_tests += 1
        name = self.name + str(self.num_tests)
        try:
            tolerance = args.pop('tolerance')
        except KeyError:
            tolerance = 0.1
        test = Test(name, new_timing_test(cases, tolerance), **args)
        self.tests.append(test)
        return test

    def test(self, **args):
        """
        Add a new test using an arbitrary
        :param args:
        :return:
        """
        def decorator(func):
            test = Test(func.__name__, new_test_true(self.name, func), **args)
            self.tests.append(test)
            return test
        return decorator

    def run(self, namespace):
        """
        Run the test suite on submission.

        :param namespace: submission object
        :return: namedtuple containing marks, total_marks, feedback
        """
        submission_fun = namespace.get(self.name, None)
        if submission_fun is not None:
            results = [test(submission_fun) for test in self.tests]
            feedback = [r.feedback for r in results]
            score = sum(r.mark for r in results)

            return ExerciseFeedback(score, self.total_marks,
                                    '\n'.join(feedback))
        else:
            msg = 'Function {} was not found in submission.'
            return ExerciseFeedback(0, self.total_marks, [msg.format(self.name)])


def exercise(**args):
    """
    Create a new exercise using this function as the model solution.
    """
    def decorator(func):
        return Exercise(func, **args)
    return decorator


