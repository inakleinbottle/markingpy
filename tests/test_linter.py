from unittest import mock

import pytest

from markingpy import linter



def test_run_linter(monkeypatch):
    mocked_linter = mock.MagicMock(spec=linter.PyLinter)
    monkeypatch.setattr(linter, 'PyLinter',
                        lambda: mocked_linter)
    mocked_linter.stats = {'test' : 0}

    class sub:
        source = 'def test(): pass'
    rep = linter.linter(sub())

    mocked_linter.load_default_plugins.assert_called()
    mocked_linter.read_config_file.assert_called()
    mocked_linter.load_config_file.assert_called()
    arg = mocked_linter.set_reporter.call_args_list[0][0]
    #mocked_linter.check.assert_called_with('temp.py')

    assert isinstance(rep, linter.LinterReport)



@pytest.fixture
def mock_report():
    return linter.LinterReport()


def test_report_write(mock_report):
    mock_report.write('Test write')
    assert mock_report.content == ['Test write']
    mock_report.write('*** no write')
    assert mock_report.content == ['Test write']

def test_report_read_with_content(mock_report):
    mock_report.content = ['Test', 'Second test']
    assert mock_report.read() == 'Test\nSecond test'

def test_report_read_no_content(mock_report):
    assert mock_report.read() == 'No issues found'
