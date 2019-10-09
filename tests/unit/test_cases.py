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
from unittest import mock
from collections import namedtuple
from contextlib import redirect_stdout
from io import StringIO
from time import sleep

import pytest

from markingpy import exercise
from markingpy import cases
from markingpy import execution
from markingpy import exercises

Call = namedtuple('Call', ['args', 'kwargs'])


def call(*args, **kwargs):
    return Call(args, kwargs)


@pytest.fixture
def call_test_m():

    @exercise
    def test_func(input):
        return input

    return cases.CallTest("Run test", None, exercise=test_func)


def test_call_test_setup_common_attributes(call_test_m):
    """Test that common Test attributes correctly defaulted."""
    assert call_test_m.descr is None
    assert call_test_m.marks == 0
    assert call_test_m.name == "CallTest"


def test_call_parameters_correctly_set(call_test_m):
    """Test that call parameters are correctly defaulted."""
    assert isinstance(call_test_m.call_args, tuple)
    assert isinstance(call_test_m.call_kwargs, dict)
    assert call_test_m.call_args == ("Run test",)
    assert not call_test_m.call_kwargs


def test_create_test_execution_context(call_test_m):
    other = None
    ctx = call_test_m.create_test(other)
    assert isinstance(ctx, execution.ExecutionContext)


def test_running_of_test_method(call_test_m):
    """Test code executed in __call__."""

    def other(input):
        return "Other " + str(input)

    ctx = call_test_m.create_test(other)
    output = None
    with ctx.catch():
        output = call_test_m.run(other)
    assert output is not None
    assert output == 'Other Run test'
    # test variables on executor
    assert ctx.error is None
    assert ctx.warnings == []
    assert not ctx.stderr.getvalue()


def test_running_of_test_method_bad_function(call_test_m):
    exc = Exception("Test exception")

    def other(input):
        raise exc

    ctx = call_test_m.create_test(other)
    output = None
    with ctx.catch():
        output = call_test_m.run(other)
    assert output is None, "Test should not have run"
    # test variables on executor
    assert ctx.error[1] is exc
    assert ctx.warnings == []
    assert not ctx.stderr.getvalue()


def test_call_test_run_with_print(call_test_m):

    def other(input):
        return input

    ctx = call_test_m.create_test(other)
    output = None
    with ctx.catch():
        output = call_test_m.run(other)
    assert output is not None
    # test variables on executor
    assert ctx.error is None
    assert ctx.warnings == []
    assert not ctx.stderr.getvalue()


def test_call_test_run_through_call(call_test_m):

    def other(input):
        return "Other" + str(input)

    output = call_test_m(other)
    assert output.mark == 0, "This test should fail."
    assert isinstance(output.feedback, str), "Feedback should be string."


@pytest.fixture
def timing_test_m():

    @exercise
    def test_func(input):
        sleep(input)

    timing_cases = [
        cases.TimingCase((0.01,), {}, 0.01),
        cases.TimingCase((0.02,), {}, 0.02),
        cases.TimingCase((0.1,), {}, 0.1),
    ]
    return cases.TimingTest(timing_cases, 0.5, exercise=test_func)


def test_timing_test_setup_common_attributes(timing_test_m):
    """Test that common Test attributes correctly defaulted."""
    assert timing_test_m.descr is None
    assert timing_test_m.marks == 0
    assert timing_test_m.name == "TimingTest"


def test_timing_test_specific_attributes(timing_test_m):
    assert isinstance(timing_test_m.cases, list)
    assert len(timing_test_m.cases) == 3
    assert all(isinstance(case, cases.TimingCase) for case in timing_test_m.cases)
    assert timing_test_m.tolerance == 0.5


def test_timing_test_create_execution_context(timing_test_m):
    other = None
    ctx = timing_test_m.create_test(other)
    assert isinstance(ctx, execution.ExecutionContext)


def test_timing_test_running(timing_test_m):
    test_calls = []

    def other(input):
        test_calls.append(input)
        sleep(input)

    ctx = timing_test_m.create_test(other)
    output = None
    with ctx.catch():
        output = timing_test_m.run(other)
    assert test_calls == [0.01, 0.02, 0.1]
    assert output is not None


def test_timing_test_function_exception(timing_test_m):
    exc = cases.ExecutionFailedError("Test exception")

    def other(input):
        raise exc

    ctx = timing_test_m.create_test(other)
    output = None
    with ctx.catch():
        output = timing_test_m.run(other)
    assert output is None
    assert isinstance(ctx.error[1], cases.ExecutionFailedError)
    assert ctx.warnings == []
    assert not ctx.stderr.getvalue()


@pytest.fixture
def custom_test_m():

    @exercise
    def test_func(input):
        return input == "test"

    def custom_func():
        print("Feedback")
        res1 = test_func("test")  # True
        res2 = test_func("not test")  # false
        return res1 and not res2

    return cases.Test(custom_func, exercise=test_func)


def test_custom_test_setup_common_attributes(custom_test_m):
    """Test that common Test attributes correctly defaulted."""
    assert custom_test_m.descr is None
    assert custom_test_m.marks == 0
    assert custom_test_m.name == "custom_func"


def test_custom_test_create_execution_context(custom_test_m):
    other = None
    ctx = custom_test_m.create_test(other)
    assert isinstance(ctx, execution.ExecutionContext)


def test_custom_test_run_test_good_func(custom_test_m):

    def other(input):
        return input == "test"

    submission_stdout = StringIO()

    def wrapper(*args, **kwargs):
        with redirect_stdout(submission_stdout):
            rv = other(*args, **kwargs)
        return rv

    ctx = custom_test_m.create_test(wrapper)
    output = None
    with ctx.catch():
        output = custom_test_m.run(wrapper)
        tested_func = custom_test_m.exercise.exc_func
    assert output is not None
    assert output
    assert tested_func is not custom_test_m.exercise.func
    assert ctx.error is None
    assert ctx.warnings == []
    assert ctx.stdout.getvalue() == "Feedback\n"


@pytest.fixture
def call_test_func():

    @exercise
    def test_func(a):
        if isinstance(a, int):
            return str(a)

        elif isinstance(a, float):
            return round(a)

        elif isinstance(a, str):
            return a

        return repr(a)

    return cases.CallTest(* call(1), exercise=test_func, marks=1)


def test_call_test_running_funcs(call_test_func):
    call_sig = call(1)
    test_cases = [('1', 1), (1, 0), (1.0, 0), ('2', 0), (repr(cases), 0)]
    for ret, res in test_cases:
        test_func = mock.MagicMock(return_value=ret)
        result = call_test_func(test_func)
        test_func.assert_called_with(* call_sig.args, ** call_sig.kwargs)
        assert result.mark == res


@pytest.fixture
def mock_exercise_func():
    return mock.MagicMock()


@pytest.fixture
def mock_submission_func():
    return mock.MagicMock()


@pytest.fixture
def mock_function_exercise(mock_exercise_func):
    ex = mock.MagicMock(autospec=exercises.FunctionExercise)
    ex.func = mock_exercise_func
    return ex


@pytest.fixture
def mock_execution_context():
    ctx = mock.MagicMock(autospec=execution.ExecutionContext)
    return ctx


def test_call_test_expected_error_get_success(
    mock_execution_context, mock_function_exercise
):
    mock_function_exercise.side_effect = lambda *a, **k: RuntimeError('bad args')
    test = cases.CallTest(
        cases.Call(('bad arg',), {}),
        None,
        expects_error=RuntimeError,
        exercise=mock_function_exercise,
    )
    mock_execution_context.error = (
        RuntimeError, RuntimeError('An error occurred'), None
    )
    success = test.get_success(mock_execution_context, None)
    assert success
    mock_execution_context.error = None
    success = test.get_success(mock_execution_context, True)
    assert not success
    mock_execution_context.error = (TypeError, TypeError('A type error occurred'), None)
    success = test.get_success(mock_execution_context, True)
    assert not success
