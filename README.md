# markingpy
Tool for grading a directory of python submissions using a scheme file containing exercises. The grader supports multiple test cases and analyses code style using PyLint.

[![Build Status](https://travis-ci.com/inakleinbottle/markingpy.svg?branch=master)](https://travis-ci.com/inakleinbottle/markingpy) 

Read the full documentation at [https://markingpy.readthedocs.io](markingpy.readthedocs.io).

## Installation
Markingpy should be installed using the pip installation tool.

```sh
pip install markingpy
```

## Example usage
There are two steps to using markingpy. First is to create the marking scheme file, which should be of the following form:

```python
from markingpy import mark_scheme, exercise, PyLintChecker

# If you want to use timing tests, use 
from markingpy import TimingCase

# Initialise mark scheme configuration.
ms = mark_scheme(
    linter=PyLintChecker(),  # add a linter to the marking process
	submissions_path='submissions' # Directory to search for submissions
)


@exercise(name='Exercise 1',
	  descr='Short description for feedback')
def ex_1_function(arg1, arg2):
	"""
	Model solution for exercise 1.
	"""
	pass

# Now add the call test components

ex_1_function.add_test_call((1, 1), marks=1)
ex_1_function.add_test.call((1, 2), marks=1)

# Add a timing test using the following
cases = [
	TimingCase((1, 1), {}, 1),
	TimingCase((10, 10), {}, 3),
]
ex_1_function.timing_test(cases, marks=2)


@ex_1_function.test
def custom_test():
	"""
	Define a custom test. This test determines whether the
	submission function does any type checking during
	execution. The test is passed if the function raises
	a TypeError.

	Custom functions should return True or False for success
	or failure, respectively.
	"""
	
	# Use the function ex_1_function in the test
	# this will be replaced by the submission function
	# during testing
	try:
		out = ex_1_function(1.0, 2.0)
	except TypeError:
		return True
	return False
```

Once the marking scheme has been created, in `scheme.py` or similar, use the command line tool to begin grading submissions:
```
markingy scheme.py run
```
The results and feedback will be generated and stored in a database, and can be retrieved using the command
```
markingpy scheme.py dump directory
```
which will dump feedback files (.txt) into *directory* for each submission.

## Development setup
Clone the repository and run ``make install``. Markingpy uses ``pipenv`` to handle its dependencies.

## Additional Disclaimer
This is my first Python package that I have "released" (i.e. put on PyPI), and I would be grateful for any feedback and constructive criticisms. Contributions are certainly welcome in all forms; see below.

## Contributing

1. Fork it (<https://github.com/inakleinbottle/markingpy/fork>)
2. Create your feature branch (`git checkout -b feature/name`)
3. Commit your changes (`git commit -m 'Add some feature')
4. Push to the branch (`git push origin feature/name`)
5. Create a new Pull Request.

## Release History

 * 1.0.0
    * Reworked grader system. Tests can now be run in separate processes to provide better isolation.
    * Reworked command line interface.
    * Reorganised and improved test suite.
    * Greatly simplified marking scheme creation and exercise association.

 * 0.2.0
	* Added support to tests on arbitrary objects and their methods.
	* Various improvements to the code base. Added descriptor support
	  for test classes and exercise classes.
	* Expanded the documentation.
	* Implemented finder system for locating submissions, which currently
	  supports loading submissions from directory (as before) and SQLite 
	  databases. Planned support for server loading.

 * 0.1.0
	* First release

## Meta

Sam Morley - sam@inakleinbottle.com - [https://inakelinbottle.com](https://inakleinbottle.com)

Distributed under the GPLV3 license. See ``LICENSE`` for more information.

