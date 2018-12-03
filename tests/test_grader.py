import unittest

from markingpy.grader import Grader


class TestGrader(unittest.TestCase):
    def test_grader(self):
        with Grader('tests/samples', 'tests/scheme/scheme.py') as grader:
            grader.grade_submissions()
