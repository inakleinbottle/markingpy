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
import pytest

from markingpy import InteractionExercise, Call
from markingpy import InteractionTest


@pytest.fixture
def inter_ex():

    class DummyClass:

        def __init__(self, a, b, kw=None):
            self._hidden = 'hidden'
            self.shown = 'shown'

        def method(self, change_to):
            self.shown = change_to

    ex = InteractionExercise(DummyClass, submission_name='test_func')
    return ex


def test_object_call_behaviour(inter_ex):
    res = inter_ex(1, 2, kw='key')
    assert res == Call((1, 2), {'kw': 'key'})
    inter_ex.lock()
    res = inter_ex(1, 2, kw='key')
    assert res is not None
    assert res.__class__.__name__ == 'DummyClass'


def test_creation_of_interaction_test_object(inter_ex):
    test = inter_ex.new_test(inter_ex(1, 2, kw=True))
    assert isinstance(test, InteractionTest)
