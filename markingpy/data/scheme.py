# Sample marking scheme for python files.


from markingpy import Exercise, mark_scheme


mark_scheme(test=90.0, style=10.0, style_formula="default")


# Exercises should be derived from the
# Exercise class found in the markingpy module
class Exercise1(Exercise):
    """
    Each exercise should have its own test class.
    Test cases are given by functions defined in
    the class that start with "test_". The names
    should be descriptive of what the test does.
    """

    # The names list declares all the functions that
    # should be found in a submission file. If these
    # are not present, due to compilation errors,
    # they should be replaced by functions that fail
    # the tests
    names = ["ex1_func"]

    def set_up(self):
        """
        Perform the necessary setup
        """
        # Omit this function if no additional setup is required.
        pass

    def test_function_1(self):
        """
        The first test case for the exercise.

        Replace this text with a short, but meaningful
        description of the test to be done.
        """
        input1 = 1.0
        input2 = 2.0
        output = 3.0
        self.assertEqual(ex1_func(input1, input2), output)
