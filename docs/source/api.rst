
Marking scheme creation
-----------------------
.. module:: markingpy

.. autofunction:: exercise

.. autofunction:: mark_scheme


Exercises
---------

.. autoclass:: Exercise
    :members:

.. autoclass:: FunctionExercise
    :members:

.. autoclass:: ClassExercise
    :members:


Tests
-----

.. module:: markingpy.cases

.. autoclass:: BaseTest
    :members:

.. autoclass:: Test
    :members:

.. autoclass:: CallTest
    :members:

.. autoclass:: TimingTest
    :members:


Finders
-------

.. module:: markingpy.finders

.. versionadded:: 0.2.0

.. autoclass:: BaseFinder
    :members:

.. autoclass:: DirectoryFinder
    :members:

.. autoclass:: SQLiteFinder
    :members:

.. autoclass:: NullFinder
    :members:


Utilities
---------
.. module:: markingpy.utils

.. autofunction:: markingpy.utils.time_run

.. autofunction:: markingpy.utils.log_calls