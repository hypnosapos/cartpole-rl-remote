#!/bin/sh -e
DIR=$(dirname "$0")

cd ${DIR}

test() {

    pytest --cov=cartpole --cov-report term-missing --pep8 ##--cov-fail-under 80

}

test_e2e() {

    pip install -e .
    cartpole --help

}

_codecov() {

    codecov

}

build() {

    python setup.py sdist bdist_wheel

}

publish() {

    twine upload --skip-existing dist/*

}


# Main options
case "$1" in
  test)
        shift
        test "$@"
        exit $?
        ;;
  test_e2e)
        shift
        test_e2e "$@"
        exit $?
        ;;
  codecov)
        shift
        _codecov "$@"
        exit $?
        ;;
  build)
        shift
        build "$@"
        exit $?
        ;;
  publish)
        shift
        publish "$@"
        exit $?
        ;;
  *)
        echo "Usage: $0 {test|test_e2e|codecov|build|publish}"
        exit 1
esac
