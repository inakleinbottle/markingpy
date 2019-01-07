"""
Exercise building utilities.
"""
import logging
from io import StringIO
from functools import wraps
from unittest import TestCase, TestResult
from contextlib import contextmanager, redirect_stdout
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


def new_test_true(ex, test_func):
    @wraps(test_func)
    def tester(other):
        def test_method(self):
            with ex.set_function(other):
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

    _test_no = 0

    def __init__(self, test_func, name=None, marks=0, descr=None, **kwargs):
        self._test_no += 1
        self.test_func = test_func
        self.name = name if name else self.get_name()
        self.marks = marks
        self.descr = descr

    def get_name(self):
        return self.test_func.__name__ + '_' + str(self._test_no)

    def create_test(self, other):
        """
        Create a unittest testcase for this test.

        :return: Unittest.TestCase.
        """
        test_case = new_class(self.name, (TestCase,))
        test_case.runTest = self.test_func(other)
        return test_case

    def format_feedback(self, outcome, result, test_stdout):
        """
        Format the feedback of the test.
        :param result:
        :return:
        """
        rv = [f'Ran {self.name}: {"Pass" if outcome else "Fail"}']
        if self.descr:
            rv.append(self.descr)

        rv.extend(INDENT + line for err in result.errors
                  for line in err[1].strip().splitlines())
        rv.extend(INDENT + line.strip()
                  for line in test_stdout.getvalue().strip().splitlines())
        return '\n'.join(rv)

    def get_success(self, result):
        """
        Determine whether the test was successful
        :param result:
        :return:
        """
        success = result.wasSuccessful()
        return success

    def __call__(self, other):
        """
        Run test on specified other.
        :param other: Function to run test against.
        :return: Namedtuple containing Test, score, feedback
        """
        test = self.create_test(other)()
        result = TestResult()
        test_stdout = StringIO()
        with redirect_stdout(test_stdout):
            test.run(result)
        outcome = self.get_success(result)
        feedback = self.format_feedback(outcome, result, test_stdout)
        marks = self.marks if outcome else 0
        feedback += f'\n{INDENT}Marks: {marks}'
        return TestFeedback(self, marks, feedback)


ExerciseFeedback = namedtuple('Feedback', ('marks', 'total_marks', 'feedback'))


class Exercise:

    _ex_no = 0

    def __init__(self, func, name=None, descr=None, **args):
        self._ex_no += 1
        wraps(func)(self)
        self.tests = []
        self.num_tests = 0
        self.func = self.exc_func = func
        self.name = name if name else self.get_name()
        self.descr = descr

    def get_name(self):
        return 'Exercise {0._ex_no}: {0.func.__name__}'.format(self)

    def __call__(self, *args, **kwargs):
        return self.exc_func(*args, **kwargs)

    @contextmanager
    def set_function(self, other):
        self.exc_func = other
        try:
            yield
        finally:
            self.exc_func = self.func

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
        test = Test(new_test_equal(self, call_params, call_kwparams), **args)
        self.tests.append(test)
        return test

    def timing_test(self, *cases, **args):
        """
        Test the timing of a submission against the model.

        :param cases:
        :param args:
        :return:
        """
        try:
            tolerance = args.pop('tolerance')
        except KeyError:
            tolerance = 0.1
        logger.info(f'Adding timing test with tolerance {tolerance}')
        test = Test(new_timing_test(cases, tolerance), **args)
        self.tests.append(test)
        return test

    def test(self, **args):
        """
        Add a new test using an arbitrary
        :param args:
        :return:
        """
        def decorator(func):
            if not 'name' in args:
                args['name'] = func.__name__
            test = Test(new_test_true(self, func), **args)
            self.tests.append(test)
            return test
        return decorator

    def run(self, namespace):
        """
        Run the test suite on submission.

        :param namespace: submission object
        :return: namedtuple containing marks, total_marks, feedback
        """
        fn_name = self.func.__name__
        submission_fun = namespace.get(fn_name, None)
        logger.info(submission_fun)
        if submission_fun is not None:
            results = [test(submission_fun) for test in self.tests]
            feedback = [r.feedback for r in results]
            score = sum(r.mark for r in results)
            logger.info(f'Score for ex: {score} / {self.total_marks}')

            return ExerciseFeedback(score, self.total_marks,
                                    '\n'.join(feedback))
        else:
            msg = 'Function {} was not found in submission.'
            return ExerciseFeedback(0, self.total_marks, msg.format(self.name))


def exercise(**args):
    """
    Create a new exercise using this function as the model solution.
    """
    def decorator(func):
        return Exercise(func, **args)
    return decorator


