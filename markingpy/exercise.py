"""
Exercise building utilities.
"""
import logging
import weakref
from collections import namedtuple, abc
from functools import wraps
from contextlib import contextmanager
from inspect import isfunction, isclass

from .cases import Test, TimingTest, TimingCase, CallTest
from .utils import log_calls
from . import cases

logger = logging.getLogger(__name__)

INDENT = " " * 4

_EXERCISES = []


class ExerciseMeta(type):

    def __new__(cls, name, bases, namespace):

        if '__init__' in namespace:
            init = namespace['__init__']

            @wraps(init)
            def wrapped(self, *args, **kwargs):
                ref = weakref.ref(self, lambda r: _EXERCISES.remove(r))
                if not ref in _EXERCISES:
                    _EXERCISES.append(ref)
                return init(self, *args, **kwargs)
            namespace['__init__'] = wrapped
        return super().__new__(cls, name, bases, namespace)


class ExerciseError(Exception):
    pass


ExerciseFeedback = namedtuple("Feedback", ("marks", "total_marks", "feedback"))


class Exercise(metaclass=ExerciseMeta):
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


    def __init__(self, function_or_class, name=None, descr=None,
                 marks=None, **args):
        wraps(function_or_class)(self)
        self.tests = []
        self.num_tests = 0
        self.func = self.exc_func = function_or_class
        self.name = name if name else self.get_name()
        self.descr = descr
        self.marks = marks

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}({self.func.__name__})"

    def get_name(self):
        return f"Exercise: {self.func.__name__}"

    def __call__(self, *args, **kwargs):
        """
        Call the exercise function or submission function.

        For functions, this is the same as invoking the function.
        For classes, this function instantiates the exercise class
        or the submission class.
        """
        return self.exc_func(*args, **kwargs)

    @contextmanager
    def set_to_submission(self, submission_func):
        self.exc_func = submission_func
        try:
            yield
        finally:
            self.exc_func = self.func

    @property
    def total_marks(self):
        t_marks = sum(t.marks for t in self.tests)
        if self.marks is None:
            return t_marks
        if not t_marks == self.marks:
            raise RuntimeError('Expected number of marks does not match '
                               'computed total')
        return self.marks

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


class FunctionExercise(Exercise):

    set_function = Exercise.set_to_submission

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


class ClassExercise(Exercise):

    @log_calls('info')
    def add_method_test(self, method, call_params=None, call_kwparams=None,
                        inst_with_args=None, inst_with_kwargs=None):
        """
        Test the call of a method on the exercise class. This will create a new
        instance with the provided arguments, and then run the named method with
        the provided arguments.


        :param method: Name of method to be called. Attribute error raised if
        the method does not exist.
        :param call_params: Parameters with which to call the method
        :param call_kwparams: Keyword parameters with which to call the method
        :param inst_with_args: Parameters for instance creation
        :param inst_with_kwargs: Keyword parameters for instance creation
        :return: MethodTest object
        """
        call_params = call_params if call_params is not None else ()
        call_kwparams = call_kwparams if call_kwparams is not None else {}
        inst_with_args = inst_with_args if inst_with_args is not None else ()
        inst_with_kwargs = inst_with_kwargs if inst_with_kwargs is not None \
            else {}
        test = cases.MethodTest(method, call_params, call_kwparams,
                                inst_with_args, inst_with_kwargs)
        self.tests.append(test)
        return test


def exercise(name=None, cls=None, **args):
    """
    Create a new exercise using this function or class as the model solution.

    The decorated function or class will be wrapped by an Exercise object that
    behaves like the original object.

    Keyword arguments are forwarded to the Exercise instance.

    :param name: Name for the exercise.
    :param cls: The exercise class to be instantiated. Defaults to FunctionExercise
    if a function is decorated and ClassExercise if a class is decorated.
    """
    if isinstance(name, str):
        args["name"] = name
        name = None

    def decorator(fn):
        nonlocal cls
        if cls is None and isfunction(fn):
            cls = FunctionExercise
        elif cls is None and isclass(fn):
            cls = ClassExercise
        else:
            raise TypeError("Expecting function or class.")
        return cls(fn, **args)

    if name is None:
        return decorator
    else:
        return decorator(name)
