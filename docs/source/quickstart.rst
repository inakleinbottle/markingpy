
Quickstart
==========
There are two steps to using the markingpy tool. The first is to create the marking scheme, which contains model solutions for the exercises and the testing components. The marking scheme also contains settings for other marking components, such as style analysis, and feedback setting. The second step is using the command line tool to run the grader on the submissions. The tool has several additional options for feedback and grade storage.

A sample marking scheme file
----------------------------
A marking scheme file should contain at least two basic elements: a mark scheme configuration created using the ``mark_scheme`` function, and exercises, which are usually created by decorating functions using the ``exercise`` function. A very simple example of a marking scheme file is the following::

    from markingpy import mark_scheme, exercise
    
    ms = mark_scheme()
    
    @exercise
    def exercise_1():
        """
        First exercise.
        """
        pass
        
When the command line tool is used to grade submissions, the grader will look for a function called ``example_1`` in the submission source. The submission version of ``exercise_1`` can then be tested against the components. At present, this marking scheme doesn't contain any marking criteria.

The most basic exercise components are *call tests*. To add a call test to ``exercise_1``, which is now an ``Exercise`` object, call the ``add_test_call`` method::
    
    # as above

    exercise_1.add_test_call((arg_1, arg_2,))
    
Now when the command line tool is used, the function ``exercise_1`` from each submission will be run with the arguments ``(arg_1, arg_2)``, and the output will be compared against the model solution function, defined in the marking scheme file. (The function defined above simply returns ``None``\ .) Note that the argument of ``add_test_call`` should be a ``tuple`` containg the arguments. A more complete example of a marking scheme file is the following::

    from markingpy import mark_scheme, exercise
    
    ms = mark_scheme(style_marks=2)
    
    @exercise
    def add(a, b):
        """
        Add two numbers
        """
        return a + b
        
    add.add_test_call((1, 1), marks=1)
    add.add_test_call((1, -1), marks=1)
    
The ``marks`` keyword argument for ``add_test_call`` informs the grader that each call test is worth one mark. The final mark for the submission is simply the sum of all component marks, plus a proportion of the style marks, defined in ``mark_scheme`` (here, 2 marks are available for style). 

Running the command line tool
-----------------------------
Once the marking scheme file is written, the command line tool can be used to grade submissions using::

    markingpy scheme.py run

By default, this command will look for a directory called *submissions*, and
will run the grader on each Python (``.py``) file found in that directory.
The results and will be stored in a database ready to be distributed. A
summary of the grades can be obtained by using the command::

    markingpy scheme.py summary

The feedback can be dumped into a directoy by using the command::

    markingpy scheme.py dump

This will create a ``.txt`` file for each submission in the current directory
that contains the feedback for that submission.
