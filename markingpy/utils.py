"""
Utilities for the MarkingPy package.
"""
from contextlib import contextmanager

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
