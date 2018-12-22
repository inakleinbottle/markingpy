Quickstart
==========
The grader requires a marking scheme containing test cases that each submission should be graded against. The score for each submission is a weighted combination of a style score, calculated using PyLint, and proportion of successful tests.

A simple example of a scheme is the following::

    from markingpy import Exericse

    class Exercise1(Exercise):
        
        names = ['test_fun']

        def test_1(self):
            """A description of the test"""
            correct_output = None
            self.assertEqual(test_fun(), correct_ouput)


Each submission should consist of a single Python file containing the functions required for each exercise. These should be placed in a directory for testing.
For example, a submission to be tested by the above might contain::
    
    def test_fun():
        """
        Solution function for exercise 1.
        """
        return None

To run the grader on this submission, run::

    markingpy scheme.py submissions

where `scheme.py` is the file containing the marking scheme and `submissions` is the directory containing the submissions. Without additional options, the grader will simply compute the grades and print a summary to the terminal. 


The command line tool
---------------------
The command line is the main method for running the grader. The main arguments are the marking scheme, which should be a python file, and a directory containing the submissons. There program has various output options:

 - *--csv CSV* Output the results to a CSV file;
 - *--output DIR* Output per-submission feedback as files in DIR. 

For example::

    markingpy --output . scheme.py submissions

outputs feedback files into the current working directory.

