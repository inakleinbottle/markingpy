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
from textwrap import dedent


import pytest

import markingpy
from markingpy import markscheme
from markingpy import finders


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
        "markingpy.markscheme.open", mock.mock_open(read_data=dedent(source))
    ):
        # noinspection PyUnresolvedReferences
        ms = markscheme.MarkingScheme(finder=finders.NullFinder())
    return ms


def test_markscheme_update_config(ms):
    conf = {
        'score_style': 'percentage', 'not_in': None
    }  # should work  # should not work
    ms.update_config(conf)
    assert ms.score_style == 'percentage'
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
