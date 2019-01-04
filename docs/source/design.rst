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
          """Description of test one"""
          self.assertAlmostEqual(ex2_func(), 0.0, 1.0e-5)

      def test_ex2_func_1(self):
          """Description of second test"""
          self.assertNotEqual(ex2_func(), 1.0)




Assertions
----------
The mechanism for determining whether a test is a success or fail is determined by a series of assertions in each test. Since the Exercise class is derived from the `unittest.TestCase` class from the standard library, all of the assertions available in the unittest library are can be used for exercises. 

The basic tests correspond to the elementary equality and instance checking in Python. 

=========================  =====================
**Method**                 **Checks**
-------------------------  ---------------------
assertEqual(a,b)           `a == b`
assertNotequal(a,b)        `a != b`
assertTrue(x)              `bool(x) is True`
assertFalse(x)             `bool(x) is False`
assertIs(a, b)             `a is b`
assertNot(a, b)            `a is not b`
assertIsNone(x)            `x is None`
assertIsNotNone(x)         `x is not None`
assertIn(a, b)             `a in b`
assertNotIn(a, b)          `a not in b`
assertIsInstance(a, b)     `isinstance(a, b)`
assertNotIsInstance(a, b)  `not isinstance(a, b)`
=========================  =====================

There are also assertions for less (equal) than and greater (equal) than comparision operators.

==========================  ========================
**Method**                  **Checks**
--------------------------  ------------------------
assertGreater(a, b)         `a > b`
assertGreaterEqual(a, b)    `a >= b`
assertLess(a, b)            `a < b`
assertLessEqual(a, b)       `a <= b`  
==========================  ========================

There is also an `assertAlmostEqual` method, which tests that two numbers are equal to a given number of decimal places by computing the difference::

    class Exercise1(Exercise):

        names = []
        
        def test_almost_equal(self):
            """Test two numbers are almost equal"""
            self.assertAlmostEqual(0.5, 0.49999999, places=5)

To test that a function raises an exception, use the `assertRaises` method. The usage is slightly different from the above, in that the function and arguments should be passed to `assertRaises` as arguments::

    class Exercise1(Exercise):

        names = ['func']
        
        def test_raises_error(self):
            """Test an exception is raised"""
            self.assertRaises(Exception, func, a, b, keyword=False)


Test case functions can contain arbitrary code. To fail a test without an assertion, the `fail` method can be used. For example::

    class Exercise1(Exercise):

        name = ['func']

        def test_fail(self):
             """Fail a test"""
             self.fail(msg='You shall not pass!')







