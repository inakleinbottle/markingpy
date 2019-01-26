from unittest import mock
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import pytest

import markingpy
from markingpy import (MethodTest, MethodTimingTest, Call, Exercise, TimingCase, TestFeedback)


@pytest.fixture
def mock_ex():
    m_ex = mock.MagicMock(autospec=Exercise)
    mock_inst = mock.MagicMock()
    m_ex.return_value = mock_inst
    m_ex._instance = mock_inst
    mock_inst.method = mock.MagicMock(__name__='method', return_value='result')
    return m_ex


@pytest.fixture
def mock_subms():
    m_sub = mock.MagicMock()
    mock_inst = mock.MagicMock()
    m_sub._instance = mock_inst
    m_sub.return_value = mock_inst
    return m_sub


@pytest.fixture
def method_call(mock_ex):
    with redirect_stdout(StringIO()):
        mct = MethodTest('method',
                         (1, 2), {'kw': 3},
                         ('one', 'two'), {'kw': 'three'},
                         exercise=mock_ex)
    return mct


def test_method_test_setup(mock_ex, method_call):
    mock_ex.assert_called_with('one', 'two', kw='three')
    mock_ex._instance.method.assert_called_with(1, 2, kw=3)


def test_run(mock_ex, mock_subms, method_call):

    # successful test
    mock_subms._instance.method = mock.MagicMock(return_value='result')

    with redirect_stdout(StringIO()):
        output = method_call.run(mock_subms)

    mock_subms.assert_called_with('one', 'two', kw='three')
    mock_subms._instance.method.assert_called_with(1, 2, kw=3)
    assert output == 'result'

    # failed test
    mock_subms._instance.method = mock.MagicMock(return_value='failed')
    with redirect_stdout(StringIO()):
        output = method_call.run(mock_subms)
    mock_subms.assert_called_with('one', 'two', kw='three')
    mock_subms._instance.method.assert_called_with(1, 2, kw=3)
    assert not output == 'result'

@pytest.fixture
def patched_timer():
    def timer(func, args, kwargs):
        return float(func(*args, **kwargs))

    with mock.patch('markingpy.cases.time_run', side_effect=timer) as mocked:
        yield mocked

@pytest.fixture
def method_timing(mock_ex, patched_timer):
    mock_ex._instance.method.side_effect = lambda a, b: b - a
    mock_ex._instance.method.return_value = None

    with redirect_stdout(StringIO()):
        mtt = MethodTimingTest('method',
                               [Call((1, 2), {}), Call((1, 5), {})],
                               0.5,
                               ('one', 'two'), {'kw': 'three'},
                               exercise=mock_ex)
    return mtt


def test_method_timing_setup(mock_ex, method_timing):
    assert all(isinstance(c, TimingCase) for c in method_timing.cases)
    mock_ex.assert_called_with('one', 'two', kw='three')


def test_run_timing_test_component(mock_ex, method_timing, patched_timer):

    other_instance = mock.MagicMock()
    other_instance.method.side_effect = lambda a, b: b - a
    other = mock.MagicMock(return_value=other_instance)

    with redirect_stdout(StringIO()):
        result = method_timing.run(other)

    assert patched_timer.call_args_list == [
        ((mock_ex._instance.method, (1, 2), {}), {}),
        ((mock_ex._instance.method, (1, 5), {}), {}),
        ((other_instance.method, (1, 2), {}), {}),
        ((other_instance.method, (1, 5), {}), {}),
    ]

    assert result