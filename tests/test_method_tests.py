from unittest import mock
import pytest


from markingpy import MethodTest, MethodTimingTest, Call, Exercise, TimingCase

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
    output = method_call.run(mock_subms)

    mock_subms.assert_called_with('one', 'two', kw='three')
    mock_subms._instance.method.assert_called_with(1, 2, kw=3)
    assert output == 'result'

    # failed test
    mock_subms._instance.method = mock.MagicMock(return_value='failed')
    output = method_call.run(mock_subms)
    mock_subms.assert_called_with('one', 'two', kw='three')
    mock_subms._instance.method.assert_called_with(1, 2, kw=3)
    assert not output == 'result'


@pytest.fixture
def method_timing(mock_ex):
    mtt = MethodTimingTest('method',
                           [Call((1,2), {}), Call((1, 5), {})],
                           0.5,
                           ('one', 'two'), {'kw': 'three'},
                           exercise=mock_ex)
    return mtt


def test_method_timing_setup(mock_ex, method_timing):
    assert all(isinstance(c, TimingCase) for c in method_timing.cases)
    mock_ex.assert_called_with('one', 'two', kw='three')
