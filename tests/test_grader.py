import unittest

from markingpy.grader import Grader
from markingpy.cli import load_config

class TestGrader(unittest.TestCase):

    def setUp(self):
        self.config = load_config()
        
    def test_grader(self):
        with Grader('tests/samples', 'tests/scheme/scheme.py', self.config) as grader:
            grader.grade_submissions()
