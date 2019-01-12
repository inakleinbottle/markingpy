
.PHONY: test
.PHONY: build
.PHONY: install-dev
.PHONY: clean-pyc
.PHONY: docs
.PHONY: install

all: test

test: clean-pyc install-dev
	pytest tests

install-dev: clean-pyc
	pip install -e .

coverage: clean-pyc install-dev
	coverage run -m pytest test
	coverage report
	coverage html

install: install-dev

test-all: install-dev
	tox

docs: clean-pyc install-dev
	$(MAKE) -C docs html

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

publish: build
	pip install 'twine>=1.50'
	twine upload dist/*
	rm -rf build dist .egg markingpy.egg-info

build:
	python setup.py sdist bdist_wheel
