# Test submission objects




from unittest import TestCase
from unittest.mock import patch, mock_open, MagicMock

from textwrap import dedent

from markingpy.submission import Submission, build_style_calc


class TestStyleCalculator(TestCase):


    def test_style_calc_builder(self):
        """Test the style calculator factory."""

        test_dict = {'error' : 1,
                     'warning' : 2,
                     'refactor' : 0,
                     'convention' : 4,
                     'statement' : 15
                    }

        calc = build_style_calc('(error + warning + refactor + convention)'
                                '/statement')

        self.assertEqual(calc(test_dict), 7/15)



class TestSubmission(TestCase):


    def setUp(self):
        source = dedent("""
                        def test_1(a, b):
                            return a + b

                        def test_2(a, b):
                            return a * b
                        """)
        
        patcher = patch('builtins.open', mock_open(read_data=source))
        
        self.mock_open = patcher.start()
        self.addCleanup(patcher.stop)
        
        self.submission = Submission('test_path')


    def test_compilation_and_report(self):
        """Test compilation and reporting."""
        try:
            self.submission.compile()
        except Exception:
            self.fail()
        self.assertIn('compilation', self.submission.feedback)


    def test_score_calculation(self):
        """Test score calculation."""
        style = MagicMock()
        style.stats = {'statement' : 5,
                       'error' : 0,
                       'warning' : 1,
                       'convention' : 2,
                       'refactor' : 1,
                       }
        self.submission.add_feedback('style', style)
        tests = MagicMock()
        tests.all_tests = [('SUCCESS',),
                           ('SUCCESS',),
                           ('SUCCESS',),
                           ('FAILED',),
                           ('FAILED',),
                           ]
        self.submission.add_feedback('test', tests)
        expected_score = 2.0 + 90*3/5
        self.assertEqual(self.submission.score, expected_score)

        
        
        