Designing Exercises
===================
MarkingPy aims to make it as easy as possible to design marking schemes. The
principle components of a marking scheme are the exercises. Each exercise
acts as a container for various marking components, called *tests*, which
test the execution of submission code in various ways.


Call tests
----------


literal block::

    from markingpy import exercise, mark_scheme

    ms = mark_scheme(
        submission_path='submissions'
    )

    @exercise(name='Exercise one')
    def ex_1(param):
        """
        Exercise one model solution.
        """
        pass

    call_parameters = (None,) # tuple of args
    call_kwparams = {} # dictionary of keyword args
    ex_1.add_test_call(call_parameters, call_kwparams,
                       name='Test name', marks=1,
                       descr='Short description for feedback')

