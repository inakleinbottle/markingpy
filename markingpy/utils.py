"""
Utilities for the MarkingPy package.
"""
import ast
import logging
from contextlib import contextmanager
from functools import wraps
from inspect import isfunction, Signature, Parameter, stack
from time import time

try:
    import resource
except ImportError:
    resource = None
try:
    import signal
except ImportError:
    signal = None
from .config import LOGGING_LEVELS

logger = logging.getLogger(__name__)
__all__ = [
    'log_calls',
    'build_style_calc',
    'DEFAULT_STYLE_FORMULA',
    'time_run',
    'str_format_args',
    'TestCaseFunction',
]
POS_OR_KW = Parameter.POSITIONAL_OR_KEYWORD


# noinspection PyPep8Naming
class GetArgumentVisitor(ast.NodeVisitor):
    _names = set()
    _func_names = set()

    def visit_Call(self, node):
        self._func_names.add(node.func.id)
        self.generic_visit(node)

    def visit_Name(self, node):
        self._names.add(node.id)
        self.generic_visit(node)

    def get_names(self):
        names = self._names - self._func_names
        self.reset()
        return names

    @classmethod
    def reset(cls):
        cls._names = set()
        cls._func_names = set()


class TestCaseFunction:
    """
    Simple function type accepting a single expression. Calls to the
    resulting function returns the evaluated expression.

    This is essentially a wrapper around a Python lambda expression.

    :param expr: Expression to evaluate on call.
    """

    def __init__(self, expr):
        self.expr = expr
        self.code = compile(expr, '<expr>', 'eval')
        visitor = GetArgumentVisitor()
        visitor.visit(ast.parse(expr, '<expr>', 'eval'))
        var_list = sorted(visitor.get_names())
        sig = Signature([Parameter(name, POS_OR_KW) for name in var_list])
        self.__signature__ = sig

    def __call__(self, *args, **kwargs):
        locs = self.__signature__.bind(*args, **kwargs)
        return eval(self.code, stack()[1][0].f_globals, locs.arguments)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.expr})'

    def __str__(self):
        return self.expr


def log_calls(level=None):
    if isfunction(level):
        fn = level
        level = logging.DEBUG
    else:
        assert level in LOGGING_LEVELS
        level = LOGGING_LEVELS[level]
        fn = None

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            msg = (
                f'Call {func.__name__}' f'({str_format_args(args, kwargs)})'
            )
            logger.log(level, msg)
            return func(*args, **kwargs)

        return wrapper

    if fn is not None:
        return decorator(fn)

    else:
        return decorator


class RunTimeoutError(Exception):
    pass


def time_exceeded():
    raise RunTimeoutError


def build_style_calc(formula):
    """
    Build a style calculator by providing a formula
    """

    def calculator(report):
        try:
            return max(0.0, eval(formula, report.stats))

        except ZeroDivisionError:
            return 0.0

    return calculator


DEFAULT_STYLE_FORMULA = (
    "1. - float(5*error"
    " + warning"
    " + refactor"
    " + convention)"
    " / statement"
)
default_style_calc = build_style_calc(DEFAULT_STYLE_FORMULA)


def str_format_args(args, kwargs):
    """
    Format the args and kwargs of a function call.

    :param args:
    :param kwargs:
    :return:
    """
    args_msg = ', '.join(str(a) for a in args)
    if kwargs:
        args_msg += ', ' if args_msg else ''
        args_msg += ', '.join(f'{k}={v}' for k, v in kwargs.items())
    return args_msg


def time_run(func, args, kwargs):
    """
    Time the running of a function.

    :param func:
    :param args:
    :param kwargs:
    :return:
    """
    start_time = time()
    func(*args, **kwargs)
    runtime = time() - start_time
    logger.debug(f"Timed run {func.__name__}: {runtime}")
    return runtime


if resource is not None and signal is not None:
    __all__.append('cpu_linit')

    @contextmanager
    def cpu_limit(limit):
        """
        Context manager, limits the CPU time of a set of commands.

        A TimeoutError is raised after the CPU time reaches the limit.

        Arguments:
            limit - The maximum number of seconds of CPU time that
                    the code can use.

        Availability: UNIX
        """
        (soft, hard) = resource.getrlimit(resource.RLIMIT_CPU)
        resource.setrlimit(resource.RLIMIT_CPU, (limit, hard))
        signal.signal(signal.SIGXCPU, time_exceeded)
        try:
            yield

        finally:
            resource.setrlimit(resource.RLIMIT_CPU, (soft, hard))


else:
    cpu_limit = None
