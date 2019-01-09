import unittest
from unittest import mock

from markingpy.cases import CallTest, TimingTest, TimingCase, Test


def null_decorator(f):
    return f

class CallTestClassTests(unittest.TestCase):

    def setUp(self):
        exercise = self.exercise = mock.MagicMock(return_value='Success')
        self.call_test = CallTest(exercise=exercise)

        # disable call logger in tests
        patcher = mock.patch('markingpy.utils.log_calls', null_decorator)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_common_attributes_set(self):
        """Test that common Test attributes correctly defaulted."""
        self.assertIsNone(self.call_test.descr)
        self.assertEqual(self.call_test.marks, 0)
        self.assertEqual(self.call_test.name, 'CallTest')

    def test_call_parameters_correct(self):
        """Test that call parameters are correctly defaulted."""
        self.assertIsInstance(self.call_test.call_args, tuple)
        self.assertEqual(self.call_test.call_args, ())
        self.assertEqual(self.call_test.call_kwargs, {})

    def test_create_test_method(self):
        """Test that test case correctly constructed."""

        def other():
            return 'Success'

        test = self.call_test.create_test(other)

        self.assertIsInstance(test, self.call_test.test_class)
        if not hasattr(test, 'runTest'):
            self.fail('Test should have a "runTest" method')







if __name__ == '__main__':
    unittest.main()
