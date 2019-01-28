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
import logging
from collections import ChainMap

logger = logging.getLogger(__name__)


class BaseDescriptor:
    cast = None

    def __init__(self, name='var', cast_to=None):
        self.name = name
        if cast_to:
            self.cast = cast_to

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


_MAGIC = {"args": ARGS, "kwargs": KWARGS, "common": DefaultGetterDescriptor}


class MagicMeta(type):

    @classmethod
    def __prepare__(cls, *args):
        return ChainMap({}, _MAGIC)

    def __new__(mcs, name, bases, namespace):
        return super().__new__(mcs, name, bases, namespace.maps[0])


class MagicBase(metaclass=MagicMeta):
    pass
