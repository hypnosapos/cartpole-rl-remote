.PHONY: help
.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build files
	@rm -rf build dist .eggs .cache docs/build
	@find . -name '*.egg-info' -exec rm -fr {} +
	@find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python build files
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage generated resources
	@rm -rf .tox .coverage htmlcov coverage-reports

test: ## run tests
	@tox

build: ## build artifacts
	@tox -e build

install: ## install
	pip install .

release: ## upload release to pypi
	@tox -e release

codecov: ## update coverage to codecov
	@tox -e codecov

doc: ## create documentation
	@tox -e doc
