
Marking scheme creation
-----------------------
.. module:: markingpy



.. autofunction:: exercise

.. autofunction:: mark_scheme


Exercises
---------

.. autoclass:: Exercise


.. autoclass:: FunctionExercise
    :members:

.. autoclass:: ClassExercise
    :members:

.. autoclass:: InteractionExercise
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


Marking Schemes
---------------

.. module:: markingpy.markscheme

.. autoclass:: MarkingScheme
    :members:

Finders
-------

.. automodule:: markingpy.finders


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