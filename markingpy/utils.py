"""
Utilities for the MarkingPy package.
"""
import logging
from contextlib import contextmanager
from time import time

logger = logging.getLogger(__name__)

try:
    import resource
except ImportError:
    resource = None

try:
    import signal
except ImportError:
    signal = None


class RunTimeoutError(Exception):
    pass


def time_exceeded():
    raise RunTimeoutError()


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


DEFAULT_STYLE_FORMULA = ('1. - float(5*error'
                         ' + warning'
                         ' + refactor'
                         ' + convention)'
                         ' / statement')
default_style_calc = build_style_calc(DEFAULT_STYLE_FORMULA)


def time_run(func, args, kwargs):
    """
    Time the running of a function.

    :param func:
    :param args:
    :param kwargs:
    :return:
    """
    start_time = time()
    try:
        func(*args, **kwargs)
    except Exception as err:
        logger.error(err)
        return None
    return time() - start_time


if resource is not None and signal is not None:

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
