import sys
from os import listdir
from os.path import join as pathjoin
from unittest import TextTestRunner
from io import StringIO

from testcases import load_tests, TestResult
from submission import Submission
from linter import linter

class Grader:
    
    def __init__(self, directory, test_file):
        self.directory = directory
        self.submissions = [Submission(pathjoin(directory, path))
                            for path in listdir(directory)
                            if path.endswith('.py')]
        with open(test_file) as f:
            self.tests = compile(f.read(), test_file, 'exec')
        self.linter = linter
        
    def grade_submission(self, submission):
        tests = load_tests(self.tests, submission.globals)
        
        stream = StringIO()
        result = TextTestRunner(stream=stream, resultclass=TestResult).run(tests)
        submission.add_feedback('test', result)
        
        report = self.linter(submission.path)
        submission.add_feedback('style', report)
        
        out_path = pathjoin(self.directory, submission.reference + '.txt')
        with open(out_path, 'w') as f:
            submission.generate_report(f)
        
    def grade_submissions(self):
        for submission in self.submissions:
            self.grade_submission(submission)
            
            
    # context manager
    def __enter__(self):
        sys.path.insert(0, self.directory)
        return self
        
    def __exit__(self, *args, **kwargs):
        sys.path.remove(self.directory)
            
            
            
if __name__ == '__main__':
    tests = 'scheme.py'
    with Grader(sys.argv[1], tests) as grader:
        grader.grade_submissions()
