import unittest

from grader import Grader


class TestGrader(unittest.TestCase):
    def test_grader(self):
        with Grader('tests/samples', 'tests/scheme.py') as grader:
            grader.grade_submissions()
