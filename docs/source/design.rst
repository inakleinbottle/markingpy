Designing Marking Schemes
=========================
MarkingPy aims to make it as easy as possible to design marking schemes. The principle components of a marking scheme are the exercises. Each exercise acts as a container for various marking components, called *tests*, which test the execution of submission code in various ways.

The suggested method for creating exercises is using the :func:`exercise` decorator. This will automatically select the appropriate :class:`Exercise` type and wrap the model solution. It is also possible to create custom exercise classes
by subclassing the :class:`Exercise` and implementing the necessary methods.

In most cases, MarkingPy exercises wrap the model solution and provide a way to execute testing code by injecting functions from each submission into the test functions. Standard exercises come in two flavours, *function exercises* and *class exercises*, to enable testing of different coding skills in Python. All exercises have three common attributes:
    :name: the name of the exercise to be displayed in feedback;
    :descr: a short description of the exercise to be displayed in feedback;
    :marks: the total number of marks available for the exercise.
Both types of exercise take a single positional argument *function_or_class*, which is the model solution object for this exercise. If the :func:`exercise` decorator is used, the relevant object is automatically passed to the
:class:`Exercise` object.

Function Exercises
------------------
To create a function exercise, apply the :func:`exercise` decorator to the relevant model solution function in the
marking scheme file::

    from markingpy import exercise

    @exercise('name', 'descr', 10)  # name, descr, marks
    def model_solution(arg1, arg2):
        """
        This is a model solution for the exercise.
        """
        # do some things
        return None

Note that MarkingPy will search for the name ``model_solution``, the name of the wrapped function, in a submission to find the function to test. This is regardless of the name attribute specified in the decorator. (The name of the function to find in each submission can be customised by providing the ``submission_name`` keyword argument to the decorator.)

By default, a function exercise is created whenever :func:`exercise` is used to decorate a function, although this behaviour can be customised by providing a ``cls`` keyword argument to :func:`exercise`. The decorated function, or class, will be wrapped in the provided class rather than the default.

Once a function exercise has been created, test components can be added using the test methods attached to the newly created objects. There are three default test component types:
        :call tests: compare the output of the submission function against the output of the model solution;
        :timing tests: compare the running time of the submission function against the running time of the model solution;
        :custom tests: a custom test provided by a user-defined function.

Call tests are the most basic test component. These are added using the ``add_test_call`` method, which takes one or two main arguments::

        test_1 = model_solution.add_test_call(model_solution(1, 2))
        test_2 = model_solution.add_test_call((1, 2), {})

The first argument should be either a tuple containing the positional arguments to be used, None (if no positional arguments are to be used), or a ``Call`` namedtuple. The latter will usually be created by calling the model solution function (as above) with the desired arguments. (In the scope of the marking scheme file, calls to the model solution function - or, more precisely, the exercise object wrapping the function - will simply return a ``Call`` namedtuple containing the arguments used in the call.) 

Timing tests are created by calling the ``timing_test`` method of the exercise object. This method takes two positional arguments specifying a list or dictionary of test cases, and the tolerance for the tests. Again, the recommended way to add cases is to simply list calls by calling the model solution::

        cases = [
            model_solution(1, 2),
            model_solution(3, 4),
            model_solution(15, 16),
            model_solution(100, 200),
        ]
        test_3 = model_solution.timing_test(cases, 0.2,
                                            name='Timing test'))

This will add a timing test with four cases, and a tolerance of 20%. When this test is created, the timing tests will be converted to ``TimingCase`` named tuples, which consist of the arguments and keyword arguments for each call, and the target time obtain by timing the execution of the model solution for each case.

Explicit target times can be added by using a dictionary rather than a list. The keys should be a tuple of arguments and keyword arguments - such as from calling ``model_solution`` - and the target time as values. For example::

        cases = {
            model_solution(1, 2): 1,
            model_solution(15, 16): 20,
            model_solution(100, 200): 40,
        }
        test_4 = model_solution.timing_test(cases, 0.2)

Custom tests can be created by writing a function decorated with the :func:`Exercise.test` decorator. The model solution function should be used within the body of this function to refer to both the model solution and the submission function during testing. The return value of this function should be a Boolean; ``True`` for a successful test, and ``False`` for an unsuccessful test. For example::

        @model_solution.test
        def test_5():
            # Custom test function

            try:
                out = model_solution(1, 2)
            except OSError:  # for example
                return True
            return False


The test objects returned in each of these cases (or the wrapped ``test_5`` function in the final case) that can be manipulated later. For example, the (display) name and description can be added, if they were not added as arguments to the creating functions.

Class Exercises
---------------
Class exercises are created in the same way, instead decorating a class (the model solution) rather than a function.
Tests can be added to instances of the model solution, which stores the arguments used to create the instance, and
the instance methods, which support test calls and timing tests. For example::

        @exercise
        class Model:

            def __init__(self, initial):
                self.value = initial

            def add(self, no):
                self.value += no
                return self.value

        first = Model(5)

        first.add.add_test_call(first.add(2), marks=1)
        first.add.add_test_call(first.add(3), marks=2)

        second = Model(3)
        second.add.add_test_call(second.add(1), marks=1)

Interactive Exercises
---------------------
Interactive exercises are different from the other exerices in that the model solution is replaced by an object,
which holds some internal state, and success criteria. For these exercises the submission function should interact
with the state object, through the methods, to meet the criteria. For example::

        @exercise(interactive=True)
        class State:

            def __init__(self):
                self._success = False

            def succeed(self):
                self._success = True

        test = State.add_test(State())

        @test.success_criterion
        def test_success(state):
            return state._success

In this example, the submission function would be required to take the state and run the succeed method to change the
state from `False` to `True`. Once the submission function returns, the exercise checks whether the success criteria
are satisfied. Marks are awarded accordingly.

The state object is not passed to the submission function directly. Instead, a proxy is passed that hides the private
attributes (those starting with `_`). The function can interact using any of the public methods.
