import unittest
from unittest import mock
from textwrap import dedent
from pathlib import Path

import pytest

import markingpy
from markingpy import markscheme



class ImportMarkschemeTests(unittest.TestCase):
    def setUp(self):
        source = """\
        from markingpy import mark_scheme, exercise
        from markingpy.finders import NullFinder
        
        ms = mark_scheme(finder=NullFinder())
        
        @exercise
        def exercise_1():
            pass
        """

        patcher = mock.patch(
            "markingpy.markscheme.open",
            mock.mock_open(read_data=dedent(source)),
        )
        self.mock_open = patcher.start()
        self.addCleanup(patcher.stop)

    @mock.patch("markingpy.markscheme.build_style_calc")
    def test_import_marksheme(self, mock_style_calc):
        """Test that mark scheme object correctly created and imported."""
        ms = markscheme.import_markscheme(Path("testpath.py"))
        self.mock_open.assert_called_with(Path("testpath.py"), "rt")
        mock_style_calc.assert_called()


@pytest.fixture
def ms():
    source = """\
           from markingpy import mark_scheme, exercise

           ms = mark_scheme()

           @exercise
           def exercise_1():
               pass
           """

    with mock.patch(
        "markingpy.markscheme.open",
        mock.mock_open(read_data=dedent(source)),
    ):
        style_formula = markingpy.utils.DEFAULT_STYLE_FORMULA
        ms = markscheme.MarkingScheme('test', [], marks_db='dbpath',
                                      submission_path='submissions',
                                      style_formula=style_formula)
    return ms


def test_markscheme_update_config(ms):
    conf = {
        'style_marks': 1,  # should work
        'not_in': None,  # should not work
    }
    ms.update_config(conf)

    assert ms.style_marks == 1
    assert not hasattr(ms, 'not_in')


def test_markscheme_score_formatter(ms):
    score = 1
    total_score = 2

    # test with basic format
    assert ms.format_return(score, total_score) == '1'

    # test with percentage
    ms.score_style = 'percentage'
    assert ms.format_return(score, total_score) == '50%'

    # test with marks/total
    ms.score_style = 'marks/total'
    assert ms.format_return(score, total_score) == '1 / 2'

    # test with all
    ms.score_style = 'all'
    assert ms.format_return(score, total_score) == '1 / 2 (50%)'

    # test with custom
    ms.score_style = '{score} - {total} ({percentage}%)'
    assert ms.format_return(score, total_score) == '1 - 2 (50%)'


def test_markscheme_run_full_marks(ms):
    """Test that markscheme.run makes correct calls to exercises and linter."""
    mock_exercise = mock.MagicMock(spec=markingpy.Exercise)
    mock_exercise.run = mock.MagicMock(return_value=(
        1,  # marks
        1,  # total marks
        'Exercise'  # feedback
    ))
    mock_submission = mock.MagicMock(autospec=markingpy.submission.Submission)
    mock_linter_report = mock.MagicMock()
    mock_linter_report.read = mock.MagicMock(return_value=(
        'Linter'
    ))
    mock_linter_report.stats = {
        'statement': 1,
        'error': 0,
        'warning': 0,
        'refactor': 0,
        'convention': 0
    }
    mock_linter = mock.MagicMock(autospec=markingpy.linter.linter,
                                 return_value=mock_linter_report)
    mock_submission.compile = mock.MagicMock(return_value=(
        'def exercise_1():\n'
        '   return None'
    ))
    ms.submissions = [mock_submission]
    ms.exercises = [mock_exercise]
    ms.linter = mock_linter

    ms.run(mock_submission)

    mock_submission.compile.assert_called()
    mock_exercise.run.assert_called()

    mock_linter.assert_called_with(mock_submission)
    mock_linter_report.read.assert_called()
    call_args_list = mock_submission.add_feedback.call_args_list
    assert call_args_list == [
        (('tests', 'Exercise'),),
        (('style', 'Linter\nStyle score: 10 / 10'),)
    ]

    assert mock_submission.percentage == 100


def test_markscheme_run_no_marks(ms):
    """Test that markscheme.run makes correct calls to exercises and linter."""
    mock_exercise = mock.MagicMock(spec=markingpy.Exercise)
    mock_exercise.run = mock.MagicMock(return_value=(
        0,  # marks
        1,  # total marks
        'Exercise'  # feedback
    ))
    mock_submission = mock.MagicMock(autospec=markingpy.submission.Submission)
    mock_linter_report = mock.MagicMock()
    mock_linter_report.read = mock.MagicMock(return_value=(
        'Linter'
    ))
    mock_linter_report.stats = {
        'statement': 4,
        'error': 1,
        'warning': 1,
        'refactor': 1,
        'convention': 1
    }
    mock_linter = mock.MagicMock(autospec=markingpy.linter.linter,
                                 return_value=mock_linter_report)
    mock_submission.compile = mock.MagicMock(return_value=(
        'def exercise_1():\n'
        '   return None'
    ))
    ms.submissions = [mock_submission]
    ms.exercises = [mock_exercise]
    ms.linter = mock_linter

    ms.run(mock_submission)

    mock_submission.compile.assert_called()
    mock_exercise.run.assert_called()

    mock_linter.assert_called_with(mock_submission)
    mock_linter_report.read.assert_called()
    call_args_list = mock_submission.add_feedback.call_args_list
    assert call_args_list == [
        (('tests', 'Exercise'),),
        (('style', 'Linter\nStyle score: 0 / 10'),)
    ]

    assert mock_submission.percentage == 0

