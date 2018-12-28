"""
Utilities for the MarkingPy package.
"""
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

try:
    import resource
except ImportError:
    resource = None

try:
    import signal
except ImportError:
    signal = None


def time_exceeded():
    raise TimeoutError()


def build_style_calc(formula):
    """
    Build a style calculator by providing a formula
    """
    def calculator(report):
        return max(0.0, eval(formula, report.stats))
    return calculator
    
DEFAULT_STYLE_FORMULA = ('1. - float(5*error'
                         ' + warning'
                         ' + refactor'
                         ' + convention)'
                         ' / statement')
default_style_calc = build_style_calc(DEFAULT_STYLE_FORMULA)

def test_calculator(report):
    all_tests = report.all_tests
    return (len(list(filter(lambda t: t[0] == 'SUCCESS', all_tests)))
            / len(all_tests))
    


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
