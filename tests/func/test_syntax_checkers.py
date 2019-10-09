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
from textwrap import dedent

import pytest

from markingpy import PyLintChecker, PyLintReport, Submission


@pytest.fixture
def submission():
    msg = '''
    def func(a, b):
        """docstring"""
        return a + b

    '''
    return Submission('submission1', dedent(msg))


def test_syntax_checker(submission):
    checker = PyLintChecker()
    report = checker.check(submission)
    assert isinstance(report, PyLintReport)
