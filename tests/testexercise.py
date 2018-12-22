# Test exercises


from unittest import TestCase
from unittest.mock import MagicMock

from types import new_class

from markingpy.exercise import Exercise, null_function



class TestExercises(TestCase):

    def setUp(self):

        def body(ns):
            ns['names'] = ['test_func', 'test_second_func']
            return ns

        self.test_class = new_class('TestExercise',
                                    (Exercise,),
                                    exec_body=body)

    def test_set_up(self):
        """Test set up hook for new exercise."""

        obj = self.test_class()
        obj.set_up = MagicMock()
        obj.setUp()

        obj.set_up.assert_called()

        

