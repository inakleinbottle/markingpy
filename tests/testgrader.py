
from unittest import TestCase
from unittest.mock import (MagicMock,
                           patch,
                           mock_open,
                           create_autospec
                          )
from textwrap import dedent


from markingpy.grader import Grader
from markingpy.submission import Submission


def _listdir(*args, **kwargs):
    return ['file%s.py' % i for i in range(10)]


TEST_EXERCISE = dedent("""
        from markingpy import Exercise, mark_scheme

        mark_scheme(
             style=10.,
             test=90.
            )

        class Ex1(Exercise):
            
            names = ['test_func']

            def test_func_1(self):
                pass


        """)



class GraderTester(TestCase):



    def setUp(self):
        
        patcher = patch('markingpy.grader.Submission',
                        autospec=True)
        self.submission_mock = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('markingpy.grader.listdir',
                        new=MagicMock(side_effect=_listdir))
        self.listdir_mock = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('markingpy.grader.open',
                        new=mock_open(read_data=TEST_EXERCISE))
        self.open_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_setup_of_grader(self):
        """Test the grader sets up correctly."""

        grader = Grader('testdir',
                        'scheme.py',
                        {'grader' : {'style_formula' : ''}})
        self.submission_mock.assert_called()
        self.open_mock.assert_called()
        self.assertEqual(grader.weighting,
                         {'style' : 10.0, 'test' : 90.0}) 
