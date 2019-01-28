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
from textwrap import dedent

import pytest

from markingpy import (
    MarkingScheme, exercise, SimpleGrader, ProcessGrader, NullFinder, Submission, Call
)


@pytest.fixture
def function_exercise():

    @exercise(name='function_exercise')
    def fn_ex(arg):
        return [arg] * 3

    fn_ex.add_test_call(fn_ex('test'), marks=1)
    return fn_ex


@pytest.fixture
def class_exercise():

    @exercise(name='class_exercise')
    class cls_ex:

        def __init__(self, no):
            self.no = no

        def meth(self, arg):
            return [arg] * self.no

    t1 = cls_ex(2)
    t1.meth.add_test_call(Call(('test',), {}), marks=1)
    return cls_ex


@pytest.fixture
def submission1():
    sub = """
    def fn_ex(arg):
        return [arg] * 3
        
    class cls_ex:
    
        def __init__(self, no):
            self.no = no
            
        def meth(self, arg):
            return [arg] * self.no
    """
    return Submission('submission1', dedent(sub))


@pytest.fixture
def submission2():
    sub = """
    def fn_ex(arg):
        return [arg] * 2

    class cls_ex:

        def __init__(self, no):
            self.no = no - 1

        def meth(self, arg):
            return [arg] * self.no
    """
    return Submission('submission2', dedent(sub))


@pytest.fixture
def finder(submission1, submission2):
    return NullFinder(submission1, submission2)


@pytest.fixture(params=(SimpleGrader(), ProcessGrader()))
def markscheme(request, function_exercise, class_exercise, finder):
    ms = MarkingScheme(grader=request.param, finder=finder)
    ms.add_exercise(function_exercise)
    ms.add_exercise(class_exercise)
    ms.validate()
    return ms


def test_grader(markscheme):
    submissions = list(markscheme.run(generate=True))
    assert len(submissions) == 2
    out = '''function_exercise
CallTest
Outcome: Pass, Marks: 1
    Testing with input: (test)
    Expected: ['test', 'test', 'test'], got: ['test', 'test', 'test']
Score for function_exercise: 1 / 1
class_exercise
MethodTest
Outcome: Pass, Marks: 1
    Testing with input: (test)
    Expected: ['test', 'test'], got: ['test', 'test']
Score for class_exercise: 1 / 1'''
    assert submissions[0].feedback['tests'] == out
    out = '''function_exercise
CallTest
Outcome: Fail, Marks: 0
    Testing with input: (test)
    Expected: ['test', 'test', 'test'], got: ['test', 'test']
Score for function_exercise: 0 / 1
class_exercise
MethodTest
Outcome: Fail, Marks: 0
    Testing with input: (test)
    Expected: ['test', 'test'], got: ['test']
Score for class_exercise: 0 / 1'''
    assert submissions[1].feedback['tests'] == out
