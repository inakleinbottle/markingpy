"""
Exercise building utilities.
"""
import logging
from collections import namedtuple
from functools import wraps
from contextlib import contextmanager
from inspect import isfunction, isclass

from .cases import Test, TimingTest, TimingCase, CallTest
from .utils import log_calls

logger = logging.getLogger(__name__)

INDENT = ' '*4


class ExerciseError(Exception):
    pass


ExerciseFeedback = namedtuple('Feedback', ('marks', 'total_marks', 'feedback'))


class Exercise:
    """
    Exercises are the main objects in a marking scheme file. These will be used
    to test each submission to construct the final mark and feedback. Each
    exercise object holds a number of tests to be run, which constitute the
    grading criteria for the exercise.

    :param function_or_class: Function or class to be wrapped.
    :param name: Name of the test. Defaults to the name of function_or_class.
    :param descr: Short description of the test to be printed in the feedback.
    """

    _ex_no = 0

    def __init__(self, function_or_class, name=None, descr=None, **args):
        self._ex_no += 1
        wraps(function_or_class)(self)
        self.tests = []
        self.num_tests = 0
        self.func = self.exc_func = function_or_class
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

    @log_calls
    def add_test_call(self, call_params=None, call_kwparams=None, **kwargs):
        """
        Add a call test to the exercise.

        Submission function is evaluated against the model solution, and is successful
        if both functions return the same value.

        :param call_params:
        :param call_kwparams:
        """
        call_params = call_params if call_params is not None else tuple()
        call_kwparams = call_kwparams if call_kwparams is not None else dict()
        test = CallTest(call_params, call_kwparams, exercise=self, **kwargs)
        self.tests.append(test)
        return test

    @log_calls
    def timing_test(self, cases, tolerance=0.2, **kwargs):
        """
        Test the timing of a submission against the model.

        :param cases:
        :param tolerance:
        :return:
        """
        if not all(isinstance(c, TimingCase) for c in cases):
            raise ExerciseError('Variable cases must be an iterable containing'
                                ' TimingCases')
        logger.info(f'Adding timing test with tolerance {tolerance}')
        logger.info(kwargs)
        test = TimingTest(cases, tolerance, exercise=self, **kwargs)
        self.tests.append(test)
        return test

    @log_calls
    def test(self, *, cls=None, **kwargs):
        """
        Add a new test using an arbitrary
        :param cls:
        :return:
        """
        if cls is None:
            cls = Test

        def decorator(func):
            test = cls(func, exercise=self, **kwargs)
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
            feedback = [self.name]
            if self.descr:
                feedback.append(self.descr)
            results = [test(submission_fun) for test in self.tests]
            feedback.extend(r.feedback for r in results)
            score = sum(r.mark for r in results)
            logger.info(f'Score for ex: {score} / {self.total_marks}')
            feedback.append('')

            return ExerciseFeedback(score, self.total_marks,
                                    '\n'.join(feedback))
        else:
            msg = 'Function {} was not found in submission.'
            return ExerciseFeedback(0, self.total_marks, msg.format(self.name))


def exercise(function_or_class=None, cls=None, **args):
    """
    Create a new exercise using this function or class as the model solution.

    The decorated function or class will be wrapped by an Exercise object that
    behaves like the original object.

    Keyword arguments are forwarded to the Exercise instance.

    :param cls: The exercise class to be instantiated.
    """
    if cls is None:
        cls = Exercise

    def decorator(fn):
        if isclass(fn):
            raise NotImplementedError('This feature is not yet implemented')
        elif isfunction(fn):
            return cls(fn, **args)
        else:
            raise TypeError('Expecting function or class.')

    if function_or_class is None:
        return decorator
    else:
        return decorator(function_or_class)


