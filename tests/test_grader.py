from unittest import mock

import pytest

from markingpy import grader
from markingpy import markscheme
from markingpy import storage
from markingpy import submission


@pytest.fixture
def mock_grader(monkeypatch):
    ms_mock = mock.MagicMock(spec=markscheme.MarkingScheme)
    submissions = [
        mock.MagicMock(
            spec=submission.Submission, reference='one', source='', percentage=100
        ),
        mock.MagicMock(
            spec=submission.Submission, reference='two', source='', percentage=0
        ),
    ]
    ms_mock.get_submissions = lambda: submissions
    db_mock = mock.MagicMock(spec=storage.Database)
    ms_mock.get_db.return_value = db_mock
    return grader.Grader(ms_mock)


def test_grader(mock_grader):
    mock_grader.grade_submissions()
    mock_grader.markscheme.run.assert_called()
