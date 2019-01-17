# Sample marking scheme for python files.
from markingpy import exercise, mark_scheme

ms = mark_scheme(submission_path="submission", style_marks=5)


# Function exercise
#
@exercise("Name of Exercise")
def first_ex(arg1, arg2, *, kwonly_arg=None):
    """
    For the first exercise, create a function that does something.

    :param arg1:
    :param arg2:
    :param kwonly_arg:
    :return:
    """
    if kwonly_arg:
        print(kwonly_arg)
    return arg1 + arg2


# Basic tests are test calls, which are added as follows.
first_ex.add_test_call((1, 2), marks=1)
# The exercise object itself can also be called to give the the parameters
first_ex.add_test_call(first_ex(-1, 2, kwonly_arg=2))
# The speed of the submission function can also be tested against the model
# solution using a timing test. A timing test needs a number of test cases.
cases = [
    first_ex(1, 1),
    first_ex(10, 10),
    first_ex(100, 100),
    first_ex(1000, 1000, kwonly_arg="Timing test"),
]
first_ex.timing_test(cases, marks=5)


# Custom tests can be defined using a the first_ex.test decorator
@first_ex.test(marks=1)
def custom_test():
    """
    Doc string will be used for short description, if none is explicitly
    provided.
    """
    try:
        # exercise object used to refer to the submission function
        output = first_ex("bad args", 2)
    except (TypeError, ValueError):
        return True  # Return True for a successful test

    return False  # Return False for unsuccessful tests




# Note: Errors that are not caught in a custom test will be propagated to
# the test executor, and the test will be failed.
# Class exercise
#
@exercise(name="Class Exercise", descr="Short description for feedback.")
class ExerciseClass:

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def method_one(self, arg):
        return self.name + ": " + self.description + ":\n" + arg

    def method_two(self, other_name):
        return self.name + ": " + other_name


instance_1 = ExerciseClass("instance_one", "First instance of the test class")
instance_1.method_one.add_test_call("try one", marks=1)
