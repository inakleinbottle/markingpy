from unittest import mock

import pytest

from markingpy import grader
from markingpy import markscheme
from markingpy import storage
from markingpy import submission


@pytest.fixture
def mock_grader(monkeypatch):
    sub_mock = mock.MagicMock(spec=submission.Submission)
    monkeypatch.setattr(grader, "Submission", sub_mock)
    ms_mock = mock.MagicMock(spec=markscheme.MarkingScheme)
    ms_mock.get_submissions.return_value = ["sub1", "sub2"]
    ms_mock.submission_path = "path"
    db_mock = mock.MagicMock(spec=storage.Database)
    ms_mock.get_db.return_value = db_mock
    return grader.Grader(ms_mock)


def test_grader(mock_grader):
    mock_grader.grade_submissions()
    mock_grader.markscheme.run.assert_called()
