from contextlib import redirect_stdout
from io import StringIO

from markingpy import mark_scheme, exercise
from markingpy.utils import time_run
from markingpy.cases import TimingCase

ms = mark_scheme(style_marks=20, score_style="all")


@exercise(descr="First task: create a function that adds two integers")
def add(a: int, b: int) -> int:
    """
    Add two integers together to get an integer.
    """

    return a + b


add.add_test_call((1, 2), marks=1)
add.add_test_call((2, 1), marks=1)
add.add_test_call((-1, 2), marks=1)
add.add_test_call((2, 4), marks=1)
cases = [(1, 1), (100, 100), (1000, 1000)]
add.timing_test(
    (TimingCase(cs, {}, time_run(add, cs, {})) for cs in cases),
    tolerance=0.2,
    marks=2,
)


#@add.test(marks=2, descr="Test Type enforcement")
def test_type_enforcement():
    """
    Test that the function only accepts integer inputs and
    returns an integer.
    """
    # float input
    a = 1.0
    b = 2.0
    stream = StringIO()
    try:
        with redirect_stdout(stream):
            returned = add(a, b)
    except Exception as err:
        feedback = (
            "Your function handled non-integer inputs"
            " by raising an exception:\n {}"
        ).format(
            err
        )
        print(feedback)
        return True

    printed = stream.getvalue()
    if returned is None and printed:
        feedback = (
            'Your function returned None and printed "{}"'
            " in response to non-integer inputs.\n"
            " It would be better to raise an exception."
        ).format(
            printed
        )
        print(feedback)
        return True

    else:
        feedback = "Your function did not enforce integer inputs."
        print(feedback)
        return False
