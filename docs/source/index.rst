.. markingpy documentation master file, created by
   sphinx-quickstart on Tue Jan  8 09:35:10 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to markingpy's documentation!
=====================================
Markingpy is a tool for automatically grading Python source file submissions, processing the results, and generating feedback reports. Markingpy uses a series of Exercise classes with attached test components to evaluate submissions, and assigns marks for each passed component. Markingpy also uses PyLint to evaluate code style, which can also be included as a graded component. 

Markingpy marking schemes are simply Python files containing  model solution functions (or classes) decorated with the ``exercise`` decorator. Test components can be added to each execise.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   design



API Reference
=============
.. toctree::
    :maxdepth: 1
    :caption: API Reference

    api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
