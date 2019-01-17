"""
Exercise building utilities.
"""
import logging
import weakref
from collections import namedtuple
from functools import wraps
from contextlib import contextmanager
from inspect import isfunction, isclass

from .cases import Test, TimingTest, CallTest, Call
from .utils import log_calls
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

    The :func:`markingpy.exercise` decorator is the preferred method for
    creating Exercise instances. This decorator will select the most
    appropriate Exercise subclass for the decorated type.

    :param function_or_class: Function or class to be wrapped.
    :param name: Name of the test. Defaults to the name of *function_or_class*.
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

    def validate(self):
        """
        Check that the exercise is valid.


        :return:
        """
        self.lock()

        total_marks = self.total_marks

        if self.marks is not None:
            if not self.marks == total_marks:
                raise ExerciseError(
                    f'{self.name} Error:\n'
                    f"Total marks ({total_marks}) from tests does not match "
                    f"marks ({self.marks}) allocated to exercise."
                )
        self.marks = total_marks

        ns = {self.func.__name__: self.func}
        result = self.run(ns)

        if not result.total_marks == self.marks:
            raise ExerciseError(
                f'{self.name} Error:\n'
                f'Total marks allocated in result ({result.total_marks}) does '
                f'not match the total marks available for the exercise '
                f'({self.marks}).'
            )

        if not result.marks == result.total_marks:
            raise ExerciseError(
                f'{self.name} Error:\n'
                f'Model solution for exercise {self.name} does not receive '
                f'full marks.\n\n{result.feedback}'
            )

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
        return sum(t.marks for t in self.tests)

    def add_test(self, *args, name=None, cls=None, **params):
        """
        Add a new test to the exercise.

        This method should usually not be called directly. It is better to
        use one of the specific test creator methods.

        Keyword parameters are passed to the Test instance.

        :param name: Name for the test. Defaults to name of the function.
        :param cls: Class to instantiate. Defaults to :class:`markingpy.Test`
        :return: Test instance
        """
        if cls is None:
            cls = Test

        test = cls(*args, exercise=self, name=name, **params)
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
        :param cls: Class to instantiate.
            Defaults to :class:`Test`.
        """
        if cls is None:
            cls = Test

        if isinstance(name, str):
            kwargs["name"] = name
            name = None

        def decorator(func):
            return self.add_test(func, name=name, cls=cls, **kwargs)

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


class ExerciseFunctionProxy:
    def add_test(self, *args, **kwargs):
        pass

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
        return self.add_test(
            call_params, call_kwparams, cls=CallTest, **kwargs
        )

    @log_calls("info")
    def timing_test(self, timing_cases, tolerance=0.2, **kwargs):
        """
        Test the timing of a submission against the model solution.

        :param timing_cases:
        :param tolerance:
        """
        return self.add_test(timing_cases, tolerance, cls=TimingTest, **kwargs)


class FunctionExercise(Exercise, ExerciseFunctionProxy):
    """
    Subclass of :class:`Exercise` with test methods for functions.

    Calling objects of this class within test functions will return the
    result of running either the model solution or the submission function

    Calling objects of this class in the body of the the marking scheme file
    will return a named tuple ``Call(args, kwargs)``, which holds the
    arguments *args* and keyword arguments *kwargs* for the call. These can
    be passed to test calls or timing tests.

    .. versionadded:: 0.2.0
    """

    set_function = Exercise.set_to_submission


class ExerciseMethodProxy(ExerciseFunctionProxy):
    def __init__(self, cls, parent, inst_call, name):
        wraps(getattr(cls, name))(self)
        self.name = name
        self.parent = parent
        self.cls = cls
        self.inst_call = inst_call

    def add_test(self, *args, cls=None, **kwargs):
        if cls is cases.CallTest:
            return self.parent.method_test_call(
                self.name,
                *args,
                inst_with_args=self.inst_call.args,
                inst_with_kwargs=self.inst_call.kwargs,
                **kwargs,
            )
        elif cls is cases.TimingTest:
            return self.parent.method_timing_test(
                self.name,
                *args,
                inst_with_args=self.inst_call.args,
                isnt_with_kwargs=self.inst_call.kwargs,
                **kwargs,
            )
        raise TypeError


# noinspection PyProtectedMember
class ExerciseInstance:
    def __init__(self, parent, cls, *args, **kwargs):
        self.__call_args = Call(args, kwargs)
        self.__parent = parent
        self.__cls = cls

    def __getattr__(self, item):
        if not hasattr(self.__cls, item):
            raise AttributeError(
                f"{self.__cls} does not have attribute {item}"
            )
        cls_attr = getattr(self.__cls, item)
        if isfunction(cls_attr):
            return ExerciseMethodProxy(
                self.__cls, self.__parent, self.__call_args, item
            )


class ClassExercise(Exercise):
    """
    Subclass of :class:`Exercise` with test methods for classes.

    This class provides two test methods specifically for testing instance
    methods for the class. The first is a method analogue for a call test on
    the :class:`FunctionExercise` class. The second is an analogue
    of a timing test.

    Calling objects of this class within test functions will return an
    instance of the model solution class or the submission class, depending
    on where this function is used.

    Calling objects of this class in the body of the the marking scheme file
    will return an instance of :class:`ExerciseInstance`,
    which provides an easier method for adding for adding method test calls and
    timing test calls to the parent exercise. Each method attached to this
    :class:`ExerciseInstance` object provides an interface similar to that of
    :class:`FunctionExercise` for adding method call tests and
    method timing tests. The arguments used to instantiate the object will
    automatically be added to the test metadata.

    .. versionadded:: 0.2.0
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def wrapper(*iargs, **ikwargs):
            return ExerciseInstance(self, self.func, *iargs, **ikwargs)

        self.exc_func = wrapper

    @log_calls("info")
    def method_test_call(
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
        :type call_params: tuple, None or :class:`Call`
        :param call_kwparams: Keyword parameters with which to call the method
        :type call_kwparams: dict or None
        :param inst_with_args: Parameters for instance creation
        :type inst_with_kwargs: dict or None
        :param inst_with_kwargs: Keyword parameters for instance creation
        :return: :class:`MethodTest` object
        """
        return self.add_test(
            method,
            call_params,
            call_kwparams,
            inst_with_args,
            inst_with_kwargs,
            cls=cases.MethodTest,
            **kwargs,
        )

    def method_timing_test(
        self,
        timing_cases,
        tolerance=0.2,
        inst_with_args=None,
        inst_with_kwargs=None,
        **kwargs,
    ):
        return self.add_test(
            timing_cases,
            tolerance,
            inst_with_args,
            inst_with_kwargs,
            cls=cases.MethodTimingTest,
            **kwargs,
        )


def exercise(name=None, cls=None, **args):
    """
    Create a new exercise using this function or class as the model solution.

    The decorated function or class will be wrapped by an Exercise object that
    behaves like the original object.

    Keyword arguments are forwarded to the Exercise instance.

    :param name: Name for the exercise.
    :type name: str
    :param cls: The exercise class to be instantiated. Defaults to
        :class:`FunctionExercise` if a function is decorated and
        :class:`ClassExercise` if a class is decorated.
    :type cls: :class:`Exercise`
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
