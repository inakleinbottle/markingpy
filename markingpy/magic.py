
import abc
import inspect
import logging
import types
from collections import ChainMap
from functools import wraps

logger = logging.getLogger(__name__)


class BaseDescriptor:
    cast = None

    def __set_name__(self, name):
        self.name = name

    def __set__(self, instance, val, typ=None):
        if self.cast is not None and val is not None:
            val = self.cast(val)
        instance.__dict__[self.name] = val


class SafeStrDescriptor(BaseDescriptor):

    def __set__(self, instance, val, typ=None):
        if isinstance(val, str):
            val = [val]
        super().__set__(instance, val, typ)


class SafeNoneDescriptor(BaseDescriptor):

    def __set__(self, instance, val, typ=None):
        if val is None:
            val = []
        super().__set__(instance, val, typ)


class ARGS(SafeNoneDescriptor, SafeStrDescriptor):
    cast = tuple


class KWARGS(SafeNoneDescriptor):
    cast = dict


class DefaultGetterDescriptor(BaseDescriptor):

    def __set__(self, instance, val, typ=None):
        if val is not None:
            return super().__set__(instance, val, typ)
        getter = getattr(instance, f'get_{self.name}', None)
        if getter is not None:
            return super().__set__(instance, getter(), typ)
        return super().__set__(instance, None, typ)


def common(cast=None):
    typ = types.new_class('NewDescriptor', (DefaultGetterDescriptor,))
    typ.cast = cast
    return typ


def method_marks(marks):
    def deco(func):
        @wraps(func)
        def wrapper(inst, *args, **kwargs):
            if not func in inst.__marked_methods:
                inst.__marked_methods[func] = marks
            return func(inst, *args, **kwargs)
        return wrapper
    return deco


_MAGIC = {'args': ARGS, 'kwargs': KWARGS, 'marks': method_marks,
          'common': common}


class MagicMeta(type):

    @classmethod
    def __prepare__(cls, *args):
        return ChainMap({}, _MAGIC)

    def __new__(mcs, name, bases, namespace):
        return super().__new__(mcs, name, bases, namespace.maps[0])


class MagicBase(metaclass=MagicMeta):

    def __init_subclass__(cls, **kwargs):
        annotations = cls.__dict__.get('__annotations__', {})
        for name, val in annotations.items():
            inst = val()
            inst.__set_name__(name)
            setattr(cls, name, inst)
        super().__init_subclass__(**kwargs)
