"""
Exercise building utilities.
"""
import functools
import logging
import weakref
from collections import namedtuple, abc
from functools import wraps
from contextlib import contextmanager
from inspect import isfunction, isclass

from .cases import Test, TimingTest, TimingCase, CallTest
from .utils import log_calls, time_run
from . import cases

logger = logging.getLogger(__name__)

INDENT = " " * 4

_exercises = weakref.WeakKeyDictionary()


class ExerciseBase:
    def __init__(self):
        ex_no = min(
            i
            for i in range(1, len(_exercises) + 2)
            if i not in _exercises.values()
        )
        _exercises[self] = ex_no

    def get_number(self):
        return _exercises[self]


class ExerciseError(Exception):
    pass


Call = namedtuple("Call", ("args", "kwargs"))
ExerciseFeedback = namedtuple("Feedback", ("marks", "total_marks", "feedback"))


def record_call(*args, **kwargs):
    return Call(args, kwargs)


class Exercise(ExerciseBase):
    """
    Exercises are the main objects in a marking scheme file. These will be used
    to test each submission to construct the final mark and feedback. Each
    exercise object holds a number of tests to be run, which constitute the
    grading criteria for the exercise.

    This class is intended to provide the core functionality for exercise
    objects, and it is not intended for this class to be instantiated
    directly. For exercises involving functions, use the subclass
    :class:`markingpy.FunctionExercise`, and for exercises involving classes
    use the subclass :class:`markingpy.ClassExercise`.

    The :function:`markingpy.exercise` decorator is the preferred method for
    creating Exercise instances. This decorator will select the most
    appropriate Exercise class to use.

    :param function_or_class: Function or class to be wrapped.
    :param name: Name of the test. Defaults to the name of function_or_class.
    :param descr: Short description of the test to be printed in the feedback.
    """

    def __init__(
        self, function_or_class, name=None, descr=None, marks=None, **args
    ):
        super().__init__()
        wraps(function_or_class)(self)
        self.tests = []
        self.number = self.get_number()
        self.num_tests = 0
        self.func = function_or_class
        self.exc_func = record_call
        self.name = name if name else self.get_name()
        self.descr = descr
        self.marks = marks

    def lock(self):
        """
        Lock the function into testing mode.

        The execution function is changed to the model function ready to be used
        for grading submissions.
        """
        # TODO: fix the tests at this point so no more can be added.
        self.exc_func = self.func

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}({self.func.__name__})"

    def get_name(self):
        return f"Exercise {self.number}: {self.func.__name__}"

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
            raise RuntimeError(
                "Expected number of marks does not match " "computed total"
            )
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
        :param cls: Class to instantiate. Defaults to :class:`markingpy.cases.Test`.
        """
        if cls is None:
            cls = Test

        if isinstance(name, str):
            kwargs["name"] = name
            name = None

        def decorator(func):
            return self.add_test(func, name, cls, **kwargs)

        if name is None:
            return decorator
        elif isfunction(name):
            return decorator(name)

    def run(self, namespace):
        """
        Run the test suite on submission.

        :param namespace: submission namespace
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
    """
    Subclass of :class:`markingpy.Exercise` with test methods for functions.
    """

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
        if isinstance(call_params, Call):
            call_params, call_kwparams = call_params
        test = CallTest(call_params, call_kwparams, exercise=self, **kwargs)
        self.tests.append(test)
        return test

    @log_calls("info")
    def timing_test(self, timing_cases, tolerance=0.2, **kwargs):
        """
        Test the timing of a submission against the model.

        :param timing_cases:
        :param tolerance:
        """
        if isinstance(timing_cases, dict):
            # cases from dict - preset targets
            timing_cases = [
                TimingCase(*call, target)
                for call, target in timing_cases.items()
                if isinstance(call, Call)
                if target > 0
            ]
        elif isinstance(timing_cases, abc.Iterable):
            # cases from iterable, each item is a separate call
            if not all(isinstance(case, TimingCase) for case in timing_cases):
                timing_cases = [
                    TimingCase(*call, time_run(self.func, *call))
                    for call in timing_cases
                    if isinstance(call, Call)
                ]
        else:
            timing_cases = None

        if not timing_cases:
            raise ExerciseError("Cases not correctly defined.")

        test = TimingTest(timing_cases, tolerance, exercise=self, **kwargs)
        logger.info(f"Adding timing test with tolerance {tolerance}")
        self.tests.append(test)
        return test


class ExerciseMethodProxy:

    def __init__(self, cls, parent, inst_call, name):
        wraps(getattr(cls, name))(self)
        self.name = name
        self.parent = parent
        self.cls = cls
        self.inst_call = inst_call

    @log_calls('info')
    def add_test_call(self, call_params=None, call_kwparams=None, **kwargs):

        if isinstance(call_params, Call):
            call_params, call_kwparams = call_params
        return self.parent.add_method_test_call(
            method=self.name,
            call_params=call_params,
            call_kwparams=call_kwparams,
            inst_with_args=self.inst_call.args,
            inst_with_kwargs=self.inst_call.kwargs,
            **kwargs
        )




# noinspection PyProtectedMember
class ExerciseInstance:

    def __init__(self, parent, cls, *args, **kwargs):
        self.__call_args = Call(args, kwargs)
        self.__parent = parent
        self.__cls = cls

    def __getattr__(self, item):
        if not hasattr(self.__cls, item):
            raise AttributeError(f'{self.__cls} does not have attribute {item}')
        cls_attr = getattr(self.__cls, item)
        if isfunction(cls_attr):
            return ExerciseMethodProxy(self.__cls, self.__parent,
                                       self.__call_args, item )


class ClassExercise(Exercise):
    """
    Subclass of :class:`markingpy.Exercise` with test methods for classes.
    """

    @log_calls("info")
    def add_method_test_call(
        self,
        method,
        call_params=None,
        call_kwparams=None,
        inst_with_args=None,
        inst_with_kwargs=None,
        **kwargs,
    ):
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
        test = cases.MethodTest(
            method,
            call_params,
            call_kwparams,
            inst_with_args,
            inst_with_kwargs,
            **kwargs,
        )
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
