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
import pytest

from markingpy import InteractionTest, Call, ExecutionContext, SuccessCriterion


@pytest.fixture
def dummy_class():

    class DummyClass:

        def __init__(self, a, b, kw=None):
            self._a = a  # hidden
            self.b = b  # visible
            self._kw = kw  # hidden

        def method(self, repl):
            self._a = repl

    return DummyClass


@pytest.fixture
def inter_tst(dummy_class):
    test = InteractionTest(dummy_class, Call((1, 2), {}))
    return test


def test_create_proxy_ns(inter_tst):
    ns = {}
    inter_tst.create_proxy_ns(ns)
    assert list(ns) == ['__getattr__', '__setattr__']


def test_create_instance_proxy(inter_tst):
    proxy = inter_tst.create_instance_proxy()
    assert proxy.b == 2
    # test setattr works
    proxy.b = 3
    assert proxy.b == 3
    # assert that proxy does not have properties _a and _kw
    with pytest.raises(AttributeError):
        b = proxy._b
    with pytest.raises(AttributeError):
        kw = proxy._kw


def test_success_criterion(inter_tst):

    @inter_tst.success_criterion
    def sc(obj):
        return obj._a > 1

    assert len(inter_tst.success_criteria) == 1
    criterion = inter_tst.success_criteria[0]
    assert isinstance(criterion, SuccessCriterion)
    assert criterion == SuccessCriterion(None, None, None, sc)

    # Test with non-keyword name
    @inter_tst.success_criterion('criterion')
    def sc2(obj):
        return obj.b

    assert len(inter_tst.success_criteria) == 2
    criterion = inter_tst.success_criteria[1]
    assert isinstance(criterion, SuccessCriterion)
    assert criterion == SuccessCriterion('criterion', None, None, sc2)

    # Test with keyword name
    @inter_tst.success_criterion(name='criterion')
    def sc3(obj):
        return obj.b

    assert len(inter_tst.success_criteria) == 3
    criterion = inter_tst.success_criteria[2]
    assert isinstance(criterion, SuccessCriterion)
    assert criterion == SuccessCriterion('criterion', None, None, sc3)

    # Test with keyword not and no name
    @inter_tst.success_criterion(marks=1)
    def sc4(obj):
        return obj.b

    assert len(inter_tst.success_criteria) == 4
    criterion = inter_tst.success_criteria[3]
    assert isinstance(criterion, SuccessCriterion)
    assert criterion == SuccessCriterion(None, None, 1, sc4)

    # Test with mixed
    @inter_tst.success_criterion('criterion', 'descr', marks=1)
    def sc5(obj):
        return obj.b

    assert len(inter_tst.success_criteria) == 5
    criterion = inter_tst.success_criteria[4]
    assert isinstance(criterion, SuccessCriterion)
    assert criterion == SuccessCriterion('criterion', 'descr', 1, sc5)


def test_create_test(inter_tst):
    ctx = inter_tst.create_test( lambda: None)
    assert isinstance(ctx, ExecutionContext)


def test_get_success(inter_tst):
    crt = SuccessCriterion(None, None, None, lambda o: o.success)
    inter_tst.success_criteria.append(crt)
    ctx = ExecutionContext()
    obj = mock.MagicMock()
    # succesful
    ctx.ran_successfully = True
    obj.success = True
    assert inter_tst.get_success(ctx, obj)
    # Fail
    ctx.ran_successfully = False
    assert not inter_tst.get_success(ctx, obj)
    ctx.ran_successfully = True
    obj.success = False
    assert not inter_tst.get_success(ctx, obj)
    ctx.ran_successfully = False
    obj.success = False
    assert not inter_tst.get_success(ctx, obj)
    obj = None
    assert not inter_tst.get_success(ctx, obj)


def test_run(inter_tst, dummy_class):

    def other(obj):
        obj.method(2)

    obj = inter_tst.run(other)
    assert isinstance(obj, dummy_class)
    assert obj._a == 2
    assert obj.b == 2
    assert obj._kw == None
