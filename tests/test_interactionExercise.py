

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
    res = inter_ex(1,2, kw='key')
    assert res == Call((1,2), {'kw': 'key'})
    inter_ex.lock()
    res = inter_ex(1, 2, kw='key')
    assert res is not None
    assert res.__class__.__name__ == 'DummyClass'


def test_creation_of_interaction_test_object(inter_ex):
    test = inter_ex.new_test(inter_ex(1,2, kw=True))
    assert isinstance(test, InteractionTest)



