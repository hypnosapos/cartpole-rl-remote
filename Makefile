.PHONY: help clean clean-build clean-pyc clean-test artifact install docs test-all
.DEFAULT_GOAL := help

# AutoDoc
define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -rf build dist .eggs .cache docs/build
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -rf .tox .coverage htmlcov coverage-reports

test: ## run tests on every Python version with tox
	@tox

build: ## build the wheel :)
	@tox -e build

install: ## install cartpole
	pip install .

release: ## upload release to pypi
	@tox -e release

codecov: ## update coverage to codecov
	@tox -e codecov

doc: ## create documentation
	@tox -e doc