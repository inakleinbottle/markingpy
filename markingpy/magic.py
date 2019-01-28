#      Markingpy automatic grading tool for Python code.
#      Copyright (C) 2019 Sam Morley
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

        getter = getattr(instance, f"get_{self.name}", None)
        if getter is not None:
            return super().__set__(instance, getter(), typ)

        return super().__set__(instance, None, typ)


class StringFactoryDescriptor(SafeNoneDescriptor):
    cast = list
    factory = None

    def __set__(self, instance, val, typ=None):
        if isinstance(val, str) and self.factory is not None:
            return super().__set__(instance, self.factory(val), typ)

        super().__set__(instance, val, typ)


def split_by_commas(self, string):
    return [s.strip() for s in string.split(',')]


class StringSplitDescriptor(StringFactoryDescriptor):
    factory = split_by_commas


def common(cast=None):
    typ = types.new_class("NewDescriptor", (DefaultGetterDescriptor,))
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


_MAGIC = {
    "args": ARGS,
    "kwargs": KWARGS,
    "marks": method_marks,
    "common": common,
    "split_commas": StringSplitDescriptor,
}


class MagicMeta(type):

    @classmethod
    def __prepare__(cls, *args):
        return ChainMap({}, _MAGIC)

    def __new__(mcs, name, bases, namespace):
        return super().__new__(mcs, name, bases, namespace.maps[0])


class MagicBase(metaclass=MagicMeta):

    def __init_subclass__(cls, **kwargs):
        annotations = cls.__dict__.get("__annotations__", {})
        for name, val in annotations.items():
            inst = val()
            inst.__set_name__(name)
            setattr(cls, name, inst)
        super().__init_subclass__(**kwargs)
