Desiging Exercises
==================
The most crucial part of running the grader is the design of a marking scheme. This should be a Python file containing a collection of tests to be run on each submission. 

The Exercise class
------------------
The `Exercise` class should be used to create exercise tests. Each exercise can contain any number of tests, but each distinct exercise should have its own object.
For example, if the work contains two exercises, then the marking scheme might contain the following::

    from markingpy import Exercise

    class Exercise1(Exercise):
        
        names = ['ex1_func']

        def set_up(self):
            """
            Perform the setup operations for exercise 1.
            """
            do_some_stuff()

        def test_ex1_func_1(self):
            """Description of first test"""
            self.assertTrue(ex1_func())

        def test_ex1_func_2(self):
            """Description of second test"""
            self.assertFalse(ex1_func())

    class Exercise2(Exercise):
        

        names = ['ex2_func']


        def test_ex2_func_1(self):
            """
            Description of test one.
            """
            self.assertAlmostEqual(ex2_func(), 0.0, 1.0e-5)

        def test_ex2_func_1(self):
            """
            Description of second test.
            """
            self.assertNotEqual(ex2_func(), 1.0)




Assertions
----------
The mechanism for determining whether a test is a success or fail is determined by a series of assertions in each test.


