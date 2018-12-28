"""
Exercise building utilities.
"""
import logging
from io import StringIO
from unittest import (TestCase, 
                      TextTestRunner,
                      TestSuite,
                      TestResult,
                      defaultTestLoader
                     )


from inspect import stack, currentframe, isclass

logger = logging.getLogger(__name__)


def mark_scheme(**components):
    """
    Declare the parameters for the marking scheme.
    """
    stack()[1][0].f_globals['scheme'] = components

class TestResult(TestResult):
    """
    Class to hold results of exercises.
    """

    def __init__(self, stream, descriptions, verbosity):
        """
        Constructor.
        """
        super(TestResult, self).__init__(stream, descriptions, verbosity)
        self.all_tests = []
        self.descriptions = descriptions

    def addSuccess(self, test):
        """
        Add a successful test to the result.
        """
        super(TestResult, self).addSuccess(test)
        if test is not None:
            self.all_tests.append(('SUCCESS', test, None))

    def addError(self, test, err):
        """
        Add an error to the result.
        """
        if test is not None:
            self.all_tests.append(('ERROR', test, err))

    def addFailure(self, test, err):
        """
        Add failed test to the result.
        """
        super(TestResult, self).addFailure(test, err)
        if test is not None:
            self.all_tests.append(('FAILED', test, err))

    def addSubTest(self, test, subtest, err):
        """
        Add a subtest to the result.
        """
        super(TestResult, self).addSubTest(test, subtest, err)
        if err is not None:
            if issubclass(err[0], test.failureException):
                result = 'FAIL'
            else:
                result = 'ERROR'
                err = err[0]
        else:
            result = 'SUCCESS'
        self.all_tests.append((result, subtest, err))

    def addSkip(self, test, reason):
        """
        Add a skipped test to the result.
        """
        super(TestResult, self).addSkip(test, reason)
        #print('SKIP: %s' % str(test))

    def getDescription(self, test):
        """
        Get the description of a test.
        """
        doc_first_line = test.shortDescription()
        if self.descriptions and doc_first_line:
            return str(test) + ' ' + doc_first_line
        else:
            str(test)

def load_tests(tests, submission_globals):
    """
    Load the tests from a file.
    """
    _globals = submission_globals.copy()
    exec(tests, _globals)
    test_cls = [cls for name, cls in _globals.items()
                if isclass(cls)
                if issubclass(cls, Exercise)
               ]
    if not test_cls:
        raise RuntimeError('No tests found in %s' % test_file)

    suite = TestSuite()
    for cls in test_cls:
        test_names = defaultTestLoader.getTestCaseNames(cls)
        suite.addTests(map(cls, test_names))
    return suite

def run_tests(test_source, submission):
    """
    Run a suite of tests on a dictionary of names.
    """
    suite = load_tests(test_source, submission.globals)
    stream = StringIO()
    return TextTestRunner(stream=stream,
                          resultclass=TestResult
                         ).run(suite)
    
    
    
    



def null_function(*args, **kwargs):
    """
    Null function used to replace non-existent names
    in the global namespace during tests.
    """
    return None


class Exercise(TestCase):
    """
    Exercise test case class for grading work.

    Test case ensures that the required functions
    are defined in the current global scope.
    """

    names = []

    def setUp(self):
        glbs = stack()[1][0].f_globals
        for name in self.names:
            if name not in glbs:
                glbs[name] = null_function
        self.set_up()


    def set_up(self):
        """
        Perform the necessary setup for the test.

        Overwrite in subclasses as necessary.
        """
        pass
