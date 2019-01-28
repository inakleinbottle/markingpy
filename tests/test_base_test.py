from unittest.mock import MagicMock, patch
from warnings import WarningMessage

import pytest

from markingpy import cases
from markingpy import execution

ExecutionCtx = object()

class ConcreteBaseTest(cases.BaseTest):
    """
    Concrete subclass of BaseTest to test the common functionality

    """

    def run(self, other):
        return None

    def create_test(self, other):
        return ExecutionCtx

@pytest.fixture
def concrete_base():
    return ConcreteBaseTest(name='Name', descr='Descr', marks=1)


def test_get_name(concrete_base):
    assert concrete_base.get_name() == 'ConcreteBaseTest'


def test_common_attributes(concrete_base):
    assert concrete_base.name == 'Name'
    assert concrete_base.descr == 'Descr'
    assert concrete_base.marks == 1


def test_create_test(concrete_base):
    assert concrete_base.create_test(lambda: None) is ExecutionCtx


def test_get_success(concrete_base):
    ctx = MagicMock(ran_successfully=True)
    assert concrete_base.get_success(ctx, True)
    assert not concrete_base.get_success(ctx, False)

    ctx.ran_successfully = False
    assert not concrete_base.get_success(ctx, True)
    assert not concrete_base.get_success(ctx, False)


def test_get_marks(concrete_base):
    concrete_base.marks = 1

    ctx = MagicMock(ran_successfully=True)
    assert concrete_base.get_marks(ctx, True, True) == 1
    assert concrete_base.get_marks(ctx, True, False) == 0


def test_format_error(concrete_base):
    err = (RuntimeError, RuntimeError(
        'This is a runtime error\n'
        'with a linebreak'
    ), None)
    output = concrete_base.format_error(err)
    assert output == ("    This is a runtime error\n"
                      "    with a linebreak")


def test_format_warnings(concrete_base):
    warns = [WarningMessage('First warning\n'
                            'with a linebreak',
                            UserWarning, '<file>', 20)]
    output = concrete_base.format_warnings(warns)

    assert output == (
        '    First warning\n'
        '    with a linebreak'
    )

    warns.append(WarningMessage('Second warning\nwith a linebreak',
                                UserWarning, '<file>', 21))
    output = concrete_base.format_warnings(warns)
    assert output == (
        '    First warning\n'
        '    with a linebreak\n'
        '    Second warning\n'
        '    with a linebreak'
    )


def test_format_stdout(concrete_base):
    stdout = 'Test output from stdout\nwith a linebreak'
    output = concrete_base.format_stdout(stdout)
    assert output == (
        '    Test output from stdout\n    with a linebreak'
    )


# noinspection PyUnresolvedReferences
def test_format_feedback(concrete_base):
    concrete_base.get_success = MagicMock(return_value=True)
    concrete_base.get_marks = MagicMock(return_value=1)
    concrete_base.format_stdout = MagicMock(return_value='    test')
    concrete_base.format_error = MagicMock()
    concrete_base.format_warnings = MagicMock()

    ctx = MagicMock(autospec=execution.ExecutionContext)
    ctx.stdout.getvalue.return_value = 'test'
    ctx.error = None
    ctx.warnings = []

    output = concrete_base.format_feedback(ctx, True)

    assert isinstance(output, cases.TestFeedback)
    assert isinstance(output.feedback, str)
    assert isinstance(output.mark, int)
    assert output.test is concrete_base

    concrete_base.get_success.assert_called_with(ctx, True)
    concrete_base.get_marks.assert_called_with(ctx, True, True)
    concrete_base.format_stdout.assert_called_with('test')
    concrete_base.format_warnings.assert_not_called()
    concrete_base.format_error.assert_not_called()


# noinspection PyUnresolvedReferences
def test_format_feedback_with_warns_and_errors(concrete_base):
    concrete_base.get_success = MagicMock(return_value=False)
    concrete_base.get_marks = MagicMock(return_value=1)
    concrete_base.format_stdout = MagicMock(return_value='    test')
    concrete_base.format_error = MagicMock(return_value='    error')
    concrete_base.format_warnings = MagicMock(return_value='    warning')

    ctx = MagicMock(autospec=execution.ExecutionContext)
    ctx.stdout.getvalue.return_value = 'test'
    ctx.error = RuntimeError('error')
    ctx.warnings = [WarningMessage('warning', UserWarning, '<file>', 20)]

    output = concrete_base.format_feedback(ctx, True)

    assert isinstance(output, cases.TestFeedback)
    assert isinstance(output.feedback, str)
    assert isinstance(output.mark, int)
    assert output.test is concrete_base

    concrete_base.get_success.assert_called_with(ctx, True)
    concrete_base.get_marks.assert_called_with(ctx, True, False)
    concrete_base.format_stdout.assert_called_with('test')
    concrete_base.format_warnings.assert_called_with(ctx.warnings)
    concrete_base.format_error.assert_called_with(ctx.error)


