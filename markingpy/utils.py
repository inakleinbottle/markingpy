
from contextlib import contextmanager

try:
    import resource
except ImportError:
    resource = None

try:
    import signal
except ImportError:
    signal = None

class TimeoutError(Exception):
    pass

def time_exceeded():
    raise TimeoutError()



if resource is not None and signal is not None:
    
    @contextmanager
    def cpu_limit(limit):
        (soft, hard) = resource.getrlimit(resource.RLIMIT_CPU)
        resource.setrlimit(resource.RLIMIT_CPU, (limit, hard))
        signal.signal(signal.SIGXCPU, time_exceeded)
        try:
            yield
        finally:
            resource.setrlimit(resource.RLIMIT_CPU, (soft, hard))

