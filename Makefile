help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean - remove build artifacts and Python file artifacts"
	@echo "test - run tests"
	@echo "build - build a package"
	@echo "install - install requirements"
	@echo "develop - install dev requirements"

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

clean: clean-build clean-pyc

test:
	pytest

build:
	python setup.py sdist bdist_wheel

install:
	pip install -e .

develop:
	pip install -e .[dev]