import unittest
from unittest import mock

from markingpy.cases import CallTest, TimingTest, TimingCase, Test


class CallTestClassTests(unittest.TestCase):

    def setUp(self):
        exercise = self.exercise = mock.MagicMock(return_value='Success')
        self.call_test = CallTest(None, None, exercise=exercise)

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
        """Test that test case correctly constructed and ran."""
        other = mock.MagicMock(return_value='Success')
        test = self.call_test.create_test(other)

    def test_testcase_run(self):
        """Test running of the test method."""
        pass


class TimingTestClassTests(unittest.TestCase):

    def setUp(self):
        exercise = self.exercise = mock.MagicMock(return_value='Success')
        self.timing_test = TimingTest((), 0.1, exercise=exercise)

    def test_common_attributes_set(self):
        """Test that common Test attributes correctly defaulted."""
        self.assertIsNone(self.timing_test.descr)
        self.assertEqual(self.timing_test.marks, 0)
        self.assertEqual(self.timing_test.name, 'TimingTest')

    def test_call_parameters_correct(self):
        """Test that call parameters are correctly defaulted."""
        pass

    def test_create_test_method(self):
        """Test that test case correctly constructed and ran."""
        pass


class GenericTestClassTests(unittest.TestCase):

    def setUp(self):
        exercise = self.exercise = mock.MagicMock(return_value='Success')
        test_func = self.test_func = mock.MagicMock()
        test_func.__name__ = 'test_func'
        self.test = Test(test_func, exercise=exercise)

    def test_common_attributes_set(self):
        """Test that common Test attributes correctly defaulted."""
        self.assertIsNone(self.test.descr)
        self.assertEqual(self.test.marks, 0)
        self.assertEqual(self.test.name, 'test_func')

    def test_create_test_method(self):
        """Test that test case correctly constructed and ran."""
        pass



if __name__ == '__main__':
    unittest.main()
