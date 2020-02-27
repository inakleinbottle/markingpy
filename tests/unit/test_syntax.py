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
import ast
import os
import io
from unittest import mock
from contextlib import contextmanager

import pytest

from markingpy import PyLintChecker, PyLintReport, Submission
from markingpy.syntax import count_statements
from markingpy import utils


@pytest.fixture
def submission1():
    code = """\ntest='test'\n"""
    return Submission('submission1', code)


@pytest.fixture
def messages():
    messages = [
        {
            "type": "convention",
            "module": "test.test",
            "obj": "",
            "line": 2,
            "column": 0,
            "path": "test.py",
            "symbol": "bad-continuation",
            "message": "Wrong hanging indentation before block (add 4 spaces).",
            "message-id": "C0330",
        },
        {
            "type": "refactor",
            "module": "test.test",
            "obj": "Test.get_test",
            "line": 125,
            "column": 4,
            "path": "cases.py",
            "symbol": "no-self-use",
            "message": "Method could be a function",
            "message-id": "R0201",
        },
    ]
    return messages

@pytest.fixture
def simple_source():
    return """
def function(arg1, arg2):
    if arg1:
        print(arg2)
    else:
        print(arg1)
    return None
    """

@pytest.fixture
def simple_ast_root(simple_source):
    return ast.parse(simple_source)

def test_count_statements(simple_ast_root):
    expected = 5
    assert count_statements(simple_ast_root) == expected


def test_pylint_report_get_stats(messages):
    rep = PyLintReport(messages, 3, None)
    stats = rep.get_stats()
    assert stats['convention'] == 1
    assert stats['refactor'] == 1
    assert stats['error'] == 0


def test_pylint_report_get_text_report(messages):
    rep = PyLintReport(messages, 2, None)
    expected = "\n".join(
        (
            '2: 0: C0330: Wrong hanging indentation before block (add 4 spaces).',
            '125: 4: R0201: Method could be a function',
        )
    )
    report = rep.get_text_report()
    assert report == expected


def test_pylint_report_calc_score_default():
    messages = [
        {'type': 'convention'},
        {'type': 'refactor'},
        {'type': 'warning'},
        {'type': 'error'},
    ]
    rep = PyLintReport(messages, 4, utils.default_style_calc)
    result = rep.get_score()
    assert isinstance(result, float)
    assert result == 10. - (5. + 1. + 1. + 1.)/4


def test_pylint_report_calc_score_custom():
    messages = [{'type': 'convention'}, {'type': 'convention'}]
    rep = PyLintReport(messages, 2, utils.build_style_calc('convention'))
    assert rep.get_score() == 2.


def test_pylint_checker_init():
    checker = PyLintChecker(ignore='C0330,R0201', msg_template='{msg}')
    params = checker.cli_args
    assert params == [
        '--ignore=C0330,R0201', '--msg-template={msg}', '--output-format=json'
    ]


def test_pylint_checker_init_overwrite_output():
    checker = PyLintChecker(output_format='text')
    params = checker.cli_args
    assert params == ['--output-format=json']


def test_pylint_checker_prepare_file_setup(submission1):
    checker = PyLintChecker()
    with checker.prepare_file(submission1) as path:
        with open(path, 'r') as f:
            assert f.read() == "\ntest='test'\n"
    assert not os.path.exists(path)


def test_pylint_checker_check_file_call(submission1):
    checker = PyLintChecker()

    @contextmanager
    def mock_prepare(sub):
        yield 'testpath'

    checker.prepare_file = mock_prepare
    with mock.patch(
        'markingpy.syntax.py_run', return_value=(io.StringIO('[]'), io.StringIO('[]'))
    ) as py_run_mock:
        report = checker.check(submission1)
        py_run_mock.assert_called_with('testpath --output-format=json', return_std=True)
