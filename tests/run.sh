#!/bin/bash

# Find where we are meant to run the tests
TESTDIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DELENV=false

# Build a virtual environment to do the tests in
cd $TESTDIR/..
rm -rf $TESTDIR/pyvirtualenv $TESTDIR/../dist $TESTDIR/../build $TESTDIR/../pyangbind.egg-info

echo "RUNNING PACKAGING..."
python setup.py bdist_wheel sdist > /dev/null
if [ $? -ne 0 ]; then
    echo "RESULT: CANNOT RUN TESTS, BROKEN PACKAGING"
    exit
fi

echo "CREATING VIRTUALENV..."
virtualenv $TESTDIR/pyvirtualenv > /dev/null
if [ $? -ne 0 ]; then
    echo "RESULT: CANNOT RUN TESTS, BROKEN VIRTUALENV"
    exit
fi

source $TESTDIR/pyvirtualenv/bin/activate

echo "INSTALLING MODULE..."
$TESTDIR/pyvirtualenv/bin/pip install -r $TESTDIR/../requirements.txt > /dev/null
$TESTDIR/pyvirtualenv/bin/pip install -r $TESTDIR/../requirements.DEVELOPER.txt > /dev/null
$TESTDIR/pyvirtualenv/bin/pip install $TESTDIR/../dist/*.whl > /dev/null
if [ $? -ne 0 ]; then
    echo "RESULT: CANNOT RUN TESTS, BROKEN INSTALL"
    exit 127
fi

export PATH_TO_PYBIND_TEST_PYTHON="$TESTDIR/pyvirtualenv/bin/python"
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
