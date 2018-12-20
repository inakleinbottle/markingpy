"""
Utilities for loading test cases.
"""

import types
import unittest

from inspect import isclass


class TestResult(unittest.TestResult):
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
        print('SKIP: %s' % str(test))

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
                if name.startswith('Test_')]
    if not test_cls:
        raise RuntimeError('No tests found in %s' % test_file)

    suite = unittest.TestSuite()
    for cls in test_cls:
        test_names = unittest.defaultTestLoader.getTestCaseNames(cls)
        suite.addTests(map(cls, test_names))
    return suite


def test_factory(test_dict, _globals):
    """
    Generate the unit tests to run from config file.
    """
    tests = {}
    for func_name, test_params in test_dict.items():
        for i, test in enumerate(test_params):
            inputs = test['input']
            expected = test['expected']

            def test_fun(self):
                self.assertEqual(_globals[func_name](*inputs), expected)
            test_fun.__doc__ = 'Test %s with inputs %s; expected %s' % (
                func_name, ', '.join(map(str, inputs)), str(expected))
            tests['test_' + func_name + '_%s' % i] = test_fun
    cls = types.new_class('Test' + func_name,
                          (unittest.TestCase,),
                          exec_body=lambda ns: ns.update(tests))
    return cls
