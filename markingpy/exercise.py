"""
Exercise building utilities.
"""
import logging
from collections import namedtuple, abc
from functools import wraps
from contextlib import contextmanager
from inspect import isfunction, isclass

from .cases import Test, TimingTest, TimingCase, CallTest
from .utils import log_calls

logger = logging.getLogger(__name__)

INDENT = " " * 4


class ExerciseError(Exception):
    pass


ExerciseFeedback = namedtuple("Feedback", ("marks", "total_marks", "feedback"))


class Exercise:
    """
    Exercises are the main objects in a marking scheme file. These will be used
    to test each submission to construct the final mark and feedback. Each
    exercise object holds a number of tests to be run, which constitute the
    grading criteria for the exercise.

    The markingpy.exercise decorator is the preferred method for creating
    instances of this class.

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

    def __str__(self):
        return self.name

    def __repr__(self):
        return "{0.__class__.__name__}(0.func.__name__)".format(self)

    def get_name(self):
        return "Exercise {0._ex_no}: {0.func.__name__}".format(self)

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

    @log_calls("info")
    def add_test_call(self, call_params=None, call_kwparams=None, **kwargs):
        """
        Add a call test to the exercise.

        Submission function is evaluated against the model solution, and is
        successful if both functions return the same value.

        :param call_params:
        :param call_kwparams:
        """
        call_params = call_params if call_params is not None else ()
        call_kwparams = call_kwparams if call_kwparams is not None else {}
        test = CallTest(call_params, call_kwparams, exercise=self, **kwargs)
        self.tests.append(test)
        return test

    @log_calls("info")
    def timing_test(self, cases, tolerance=0.2, **kwargs):
        """
        Test the timing of a submission against the model.

        :param cases:
        :param tolerance:
        """
        if not isinstance(cases, abc.Iterable):
            raise ExerciseError("cases must be an iterable")
        if not all(isinstance(c, TimingCase) for c in cases):
            raise ExerciseError(
                "cases must be an iterable containing TimingCases"
            )
        logger.info(f"Adding timing test with tolerance {tolerance}")
        logger.info(kwargs)
        test = TimingTest(cases, tolerance, exercise=self, **kwargs)
        self.tests.append(test)
        return test

    @log_calls("info")
    def add_test(self, function, name=None, cls=None, **params):
        """
        Add a new test to the exercise. The function should return
        True for a successful test and False for a failed test.

        Keyword parameters are passed to the Test instance.

        :param function: Test function to add
        :param name: Name for the test. Defaults to name of the function.
        :param cls: Class to instantiate. Defaults to `markingpy.cases.Test`
        :return: Test instance
        """
        if cls is None:
            cls = Test

        test = cls(function, exercise=self, name=name, **params)
        self.tests.append(test)
        return test

    @log_calls("info")
    def test(self, name=None, cls=None, **kwargs):
        """
        Add a new test to the exercise by decorating a function. The function
        should return `True` for a successful test and `False` for a failed
        test. Printed statements used in the function will be added to the
        feedback for the submission.

        Equivalent to creating a function `func` and running
        `ex.add_test(func)`.

        :param name: Name for the test. Defaults to name of the function.
        :param cls: Class to instantiate. Defaults to `markingpy.cases.Test`.
        """
        if cls is None:
            cls = Test

        if isinstance(name, str):
            kwargs["name"] = name
            name = None

        def decorator(func):
            test = cls(func, exercise=self, **kwargs)
            self.tests.append(test)
            return test

        if name is None:
            return decorator
        elif isfunction(name):
            return decorator(name)

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
            logger.info(f"Score for ex: {score} / {self.total_marks}")
            feedback.append(
                f"Score for {self.name}: {score} / {self.total_marks}"
            )

            return ExerciseFeedback(
                score, self.total_marks, "\n".join(feedback)
            )
        else:
            msg = "Function {} was not found in submission."
            return ExerciseFeedback(
                0, self.total_marks, msg.format(self.func.__name__)
            )


def exercise(name=None, cls=None, **args):
    """
    Create a new exercise using this function or class as the model solution.

    The decorated function or class will be wrapped by an Exercise object that
    behaves like the original object.

    Keyword arguments are forwarded to the Exercise instance.

    :param name: Name for the exercise.
    :param cls: The exercise class to be instantiated.
    """
    if cls is None:
        cls = Exercise

    if isinstance(name, str):
        args["name"] = name
        name = None

    def decorator(fn):
        if isclass(fn):
            raise NotImplementedError("This feature is not yet implemented")
        elif isfunction(fn):
            return cls(fn, **args)
        else:
            raise TypeError("Expecting function or class.")

    if name is None:
        return decorator
    else:
        return decorator(name)
