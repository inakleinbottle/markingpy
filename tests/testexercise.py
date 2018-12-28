# Test exercises


from unittest import TestCase
from unittest.mock import MagicMock

from types import new_class
from textwrap import dedent

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
        
    def test_unavailable_function_recovery(self):
        """Test respose to unavailable function."""
        test_func = MagicMock()
        
        source = dedent('''
                        from markingpy.exercise import Exercise
                        
                        class TestExercise(Exercise):
                            names = ['test_func', 'test_second_func']
                            
                        obj = TestExercise() 
                        obj.setUp() 
                        ''')
                        
        globs = {'test_func': test_func}
        exec(source, globs)
        
        self.assertIn('test_second_func', globs)
        self.assertIs(globs['test_second_func'], null_function)        
        

        

