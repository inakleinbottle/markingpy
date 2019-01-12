# markingpy
Tool for grading a directory of python submissions using a scheme file containing exercises. The grader supports multiple test cases and analyses code style using PyLint.

[![Build Status](https://travis-ci.com/inakleinbottle/markingpy.svg?branch=master)](https://travis-ci.com/inakleinbottle/markingpy) 

## Installation
Markingpy should be installed using the pip installation tool.

```sh
pip install markingpy
```

## Example usage
There are two steps to using markingpy. First is to create the marking scheme file, which should be of the following form:

```python
from markingpy import mark_scheme, exercise

# If you want to use timing tests, use 
from markingpy import TimingCase

# Initialise mark scheme configuration.
ms = mark_scheme(
	style_marks=10, # Number of marks for coding style
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
def custom_test()
	"""
	Define a custom test. This test determines whether the
	submission function does any type checking during
	execution. The test is passed if the function raises
	a TypeError.

	Custom functions should return True or False for success
	or failure, respectively.
	"""
	
	# Use the function ex_1_function in the test
	# this will be replaced by the sumbission function
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


## Release History

 * 0.1.0
	* First release

## Meta

Sam Morley - sam@inakleinbottle.com

Distributed under the GPLV3 license. See ``LICENSE`` for more information.

[https://inakelinbottle.com](https://inakleinbottle.com)

## Contributing

1. Fork it (<https://github.com/inakleinbottle/markingpy/fork>)
2. Create your feature branch (`git checkout -b feature/name`)
3. Commit your changes (`git commit -am 'Add some feature')
4. Push to the branch (`git push origin feature/name`)
5. Create a new Pull Request.

