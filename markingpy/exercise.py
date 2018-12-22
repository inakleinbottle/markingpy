"""
Exercise building utilities.
"""

from unittest import TestCase


def null_function(*args, **kwargs):
    """
    Null function used to replace non-existent names
    in the global namespace during tests.
    """
    return None


class Exercise(TestCase):
    """
    Exercise test case class for grading work.

    Test case ensures that the required functions
    are defined in the current global scope.
    """

    names = []

    def setUp(self):
        for name in self.names:
            if name not in globals():
                globals()['name'] = null_function
        self.set_up()


    def set_up(self):
        """
        Perform the necessary setup for the test.

        Overwrite in subclasses as necessary.
        """
        pass
