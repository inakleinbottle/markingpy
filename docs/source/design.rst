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

        











literal block::

    from markingpy import exercise, mark_scheme

    mark_scheme(
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

