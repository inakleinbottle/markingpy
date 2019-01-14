import unittest
import tempfile
from unittest import mock
from textwrap import dedent
from pathlib import Path

import pytest

from markingpy import markscheme
from markingpy.finders import NullFinder


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
    with tempfile.TemporaryDirectory() as directory:
        source = """\
                 from markingpy import mark_scheme, exercise
        
                 ms = mark_scheme()
        
                 @exercise
                 def exercise_1():
                     pass
                 """
        Path(directory, 'test.py').write_text(source)
        ms = markscheme.MarkingScheme('test', [], marks_db='dbpath',
                                      submission_path=directory)

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
