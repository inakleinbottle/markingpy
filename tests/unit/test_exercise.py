#      Markingpy automatic grading tool for Python code.
#      Copyright (C) 2019 University of East Anglia
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#
# Test exercises
from collections import namedtuple
import pytest
from unittest import mock
import random

from decimal import Decimal
from fractions import Fraction
from typing import Iterable
from math import sqrt

import markingpy
from markingpy import exercises
from markingpy.exercises import ( Exercise, ExerciseFeedback)
from markingpy import cases, exercise

Call = namedtuple('Call', ['args', 'kwargs'])


def call(*args, **kwargs):
    return Call(args, kwargs)


@pytest.fixture
def no_add_exercises():
    markingpy.NO_ADD_EXERCISES = True
    return None


@pytest.fixture
def ex_no_args(no_add_exercises):

    @exercise
    def test_func(a, b):
        return "Success"

    test_func.lock()
    return test_func


@pytest.fixture
def ex_with_args(no_add_exercises):

    @exercise(name="Test 1", descr="Descr")
    def test():
        return "Also Success"

    test.lock()
    return test


def test_created_exercise_attributes(ex_no_args):
    """Test that created exercises has correct attributes."""
    assert isinstance(ex_no_args, Exercise)
    assert ex_no_args.name == f"Exercise {ex_no_args.get_number()}: test_func"
    assert ex_no_args.exc_func is ex_no_args.func
    assert ex_no_args(None, None) == "Success"
    assert ex_no_args.total_marks == 0


def test_exercise_change_function(ex_no_args):
    """Test change function context manager."""

    def other():
        pass

    assert ex_no_args.exc_func is ex_no_args.func
    with ex_no_args.set_function(other):
        assert ex_no_args.exc_func is other
    assert ex_no_args.exc_func is ex_no_args.func


def test_ex_with_args_attributes(ex_with_args):
    """Test second exercise set up correctly."""
    assert isinstance(ex_with_args, Exercise)
    assert ex_with_args.name == "Test 1"
    assert ex_with_args.descr == "Descr"
    assert ex_with_args.total_marks == 0


def test_adding_tests_to_ex(ex_with_args):
    """Test adding test functions to exercise."""
    t1 = ex_with_args.add_test_call(marks=1)
    assert isinstance(t1, markingpy.cases.CallTest)
    assert ex_with_args.total_marks == 1
    tc = markingpy.cases.TimingCase((1,), {"a": 1}, 5)
    t2 = ex_with_args.timing_test([tc], tolerance=0.2, marks=1)
    assert isinstance(t2, markingpy.cases.TimingTest)
    assert ex_with_args.total_marks == 2

    @ex_with_args.test(marks=1)
    def t3():
        return True

    assert isinstance(t3, markingpy.cases.Test)
    assert ex_with_args.total_marks == 3

    @ex_with_args.test
    def t4():
        return False

    assert isinstance(t4, markingpy.cases.Test)
    assert ex_with_args.total_marks == 3

    def fun():
        return None

    t5 = ex_with_args.add_test(fun, marks=1)
    assert isinstance(t5, markingpy.cases.Test)
    assert ex_with_args.total_marks == 4


def test_ex_add_bad_timing_tests(ex_with_args):
    """Test adding bad timing test arguments."""
    try:
        ex_with_args.timing_test(None)
        assert False, "Timing test expects iterable"
    except Exception as err:
        assert isinstance(err, ValueError)
    try:
        ex_with_args.timing_test([None])
        assert False, "Timing test expects iterable of TimingCases"
    except Exception as err:
        assert isinstance(err, ValueError)


@pytest.fixture
def ex_with_component(no_add_exercises):

    @exercise
    def test():
        return "Success"

    test.add_test_call(None, marks=1)
    test.lock()
    return test


def test_running_of_test_components_success(ex_with_component):
    """Test running of tests and feedback"""
    submission_good_func = mock.MagicMock(return_value="Success")
    ns = {"test": submission_good_func}
    out = ex_with_component.run(ns)
    assert isinstance(out, ExerciseFeedback)
    submission_good_func.assert_called()
    score, tot, fb, tr = out
    assert score == tot
    assert isinstance(fb, str)


def test_running_of_test_components_fail(ex_with_component):
    """Test running of tests and feedback"""
    submission_bad_func = mock.MagicMock(return_value="Also Success")
    ns = {"not_test": submission_bad_func}
    out = ex_with_component.run(ns)
    assert isinstance(out, ExerciseFeedback)
    submission_bad_func.assert_not_called()
    score, tot, fb, tr = out
    assert score == 0
    assert isinstance(fb, str)


def randbetween(a, b):
    return a + (b - a) * random.random()


@pytest.fixture
def calltest_cases():
    return [
        * (call(random.randint(-5, 5)) for _ in range(2)),
        * (call(randbetween(-5.0, 5.0)) for _ in range(2)),
        * (
            call(float('inf')),
            call(- float('inf')),
            call(float('nan')),
            call(- float('nan')),
        ),
        * (call(Decimal(randbetween(-5, 5))) for _ in range(2)),
        * (call(Fraction(randbetween(-5, 5))) for _ in range(2)),
        * (call(complex(randbetween(-5, 5), randbetween(-10, 10))) for _ in range(2)),
        * (call([randbetween(-5, 5) for _ in range(n)]) for n in [1, 5, 10, 90]),
        * (call(tuple(randbetween(-5, 5) for _ in range(n))) for n in [1, 5, 10, 90]),
    ]


@pytest.fixture
def multiple_test_abs_ex(calltest_cases):

    @exercise
    def abs(x):
        if isinstance(x, (float, int, Decimal, Fraction)):
            return -x if x < 0 else x

        elif isinstance(x, complex):
            return sqrt(x.real ** 2 + x.imag ** 2)

        elif isinstance(x, str):
            raise TypeError(f'Cannot take absolute value of type {type(x)}')

        elif isinstance(x, Iterable):
            cls = type(x)
            return cls(abs(x_) for x_ in x)

        else:
            raise TypeError(f'Cannot take absolute value of type {type(x)}')

    for tc in calltest_cases:
        abs.add_test_call(*tc, marks=1, name=str(tc))
    abs.lock()  # lock rather than validate
    return abs


def test_many_call_tests_ex(calltest_cases, multiple_test_abs_ex):
    from math import fabs

    def bs(x):
        if not isinstance(x, Iterable):
            return fabs(x)

        return type(x)(fabs(x_) for x_ in x)

    test_func = mock.MagicMock(side_effect=bs)
    fb = multiple_test_abs_ex.run({'abs': test_func})
    test_func.assert_called()
    assert test_func.call_args_list == calltest_cases


@pytest.fixture
def exercise_target():
    return mock.MagicMock()


@pytest.fixture
def exercise_fixture(exercise_target):
    return Exercise(
        exercise_target,
        name='exercise',
        descr='description',
        marks=5,
        submission_name='sub_func',
    )


def test_common_attributes(exercise_fixture):
    assert exercise_fixture.name == 'exercise'
    assert exercise_fixture.descr == 'description'
    assert exercise_fixture.marks == 5
    assert exercise_fixture.submission_name == 'sub_func'


def test_get_name(exercise_fixture, exercise_target):
    exercise_target.__name__ = 'target'
    assert exercise_fixture.get_name() == (
        f'Exercise {exercise_fixture.get_number()}: target'
    )


def test_unlocked_exercise_call_record(exercise_fixture):
    out = exercise_fixture('arg1', 'arg2', kw='arg3')
    assert isinstance(out, cases.Call)
    assert out.args == ('arg1', 'arg2')
    assert out.kwargs == {'kw': 'arg3'}


def test_exercise_lock(exercise_fixture, exercise_target):
    exercise_fixture.lock()
    assert exercise_fixture.exc_func is exercise_target


def test_total_marks_property(exercise_fixture):
    mcks = [mock.MagicMock(marks=i) for i in range(1, 4)]
    exercise_fixture.tests = mcks
    assert exercise_fixture.total_marks == 6


def test_exercise_validation(exercise_fixture, exercise_target):
    with pytest.raises(exercises.ExerciseError):
        exercise_fixture.validate()
    mcks = [mock.MagicMock(marks=i) for i in range(2, 4)]
    exercise_fixture.tests = mcks
    result_mock = mock.MagicMock(marks=2, total_marks=2, feedback='', per_test=[])
    exercise_fixture.run = mock.MagicMock(return_value=result_mock)
    ns = {'sub_func': exercise_target}
    with pytest.raises(exercises.ExerciseError):
        exercise_fixture.validate()
    exercise_fixture.run.assert_called_with(ns)
    result_mock.total_marks = 5
    with pytest.raises(exercises.ExerciseError):
        exercise_fixture.validate()
    result_mock.marks = 5
    exercise_fixture.validate()


def test_get_submission_func(exercise_fixture):

    def mck():
        pass

    ns = {'sub_func': mck}
    assert exercise_fixture.get_submission_function(ns) is mck
    ns = {'sub_func1': mck}
    assert exercise_fixture.get_submission_function(ns) is None


def test_custom_test_decorator(exercise_fixture):

    def func():
        pass

    wrapped = exercise_fixture.test(func)
    assert isinstance(wrapped, cases.Test)
    wrapped = exercise_fixture.test('name')(func)
    assert isinstance(wrapped, cases.Test)
    assert wrapped.name == 'name'
    assert wrapped.test_func is func
    with pytest.raises(TypeError):
        exercise_fixture.test(True)
