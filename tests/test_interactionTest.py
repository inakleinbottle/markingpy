import pytest

from markingpy import InteractionTest, Call

@pytest.fixture
def inter_tst():

    class DummyClass:

        def __init__(self, a, b, kw=None):
            self._a = a  # hidden
            self.b = b  # visible
            self._kw = kw  # hidden

        def method(self, repl):
            self._a = repl

    test = InteractionTest(DummyClass, Call((1, 2), {}))
    return test


def test_create_proxy_ns(inter_tst):
    ns = {}
    inter_tst.create_proxy_ns(ns)
    assert list(ns) == ['__getattr__', '__setattr__']


def test_create_instance_proxy(inter_tst):
    proxy = inter_tst.create_instance_proxy

    assert proxy.b == 2

    # assert that proxy does not have properties _a and _b





def test_success_criterion(inter_tst):

    @inter_tst.success_criterion
    def sc(obj):
        return obj._a > 1

    assert inter_tst.success_criterion.name = None


def test_create_test(inter_tst):
    ...

def test_get_success(inter_tst):
    ...

def test_run(inter_tst):
    ...
