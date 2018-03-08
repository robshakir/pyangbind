#!/bin/bash

# Find where we are meant to run the tests
TESTDIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DELENV=false

function runtests { 
    PYTHON_INTERPRETER=$1

    echo -n "Testing with "
    $PYTHON_INTERPRETER --version

    export PYTHONDONTWRITEBYTECODE=1

    export PATH_TO_PYBIND_TEST_PYTHON="python"
    FAIL=0

    for TEST in $TESTDIR/yang_tests.sh $TESTDIR/xpath/xpath_tests.sh $TESTDIR/serialise/serialise_tests.sh $TESTDIR/integration/integration_tests.sh; do
      $TEST
      if [ $? -ne 0 ]; then
        FAIL=1
      fi
    done

    if [ "$DELENV" == "true" ]; then
        rm -rf $TESTDIR/pyvirtualenv $TESTDIR/../dist $TESTDIR/../build $TESTDIR/../pyangbind.egg-info
    fi

    if [ $FAIL -ne 0 ]; then
      echo "OVERALL TEST RUN: Tests failed"
      exit 127
    fi
}

runtests "python"
