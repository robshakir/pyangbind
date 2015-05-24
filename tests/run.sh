#!/bin/bash
FAIL=0
TESTDIR=`pwd`
export PYANGBINDPATH=$TESTDIR/..
export PYANGPATH=`which pyang`

echo "RUNNING BASE"
$PYANGPATH --plugindir $PYANGBINDPATH -f pybind $TESTDIR/base-test.yang -o /tmp/chkplugin.pyang >/dev/null
if [ $? -ne 0 ]; then
    echo "RESULT: CANNOT RUN TESTS, BROKEN PLUGIN"
    exit
fi
rm /tmp/chkplugin.pyang

if [ $# -eq 0 ]; then
    FAIL=0
    for i in `find $TESTDIR -mindepth 1 -maxdepth 1 -type d`; do
        echo "TESTING $i..."
        $i/run.py > /dev/null
        if [ $? -ne 0 ]; then
            echo "TEST FAILED $i";
            FAIL=$((FAIL+1))
        fi
    done
    if [ $FAIL -eq 0 ]; then
        echo "RESULT: all tests passed"
    else
        echo "RESULT: $FAIL tests failed"
    fi
else
    for i in "$@"; do
        echo "TESTING $i..."
        $i/run.py > /dev/null
        if [ $? -ne 0 ]; then
            echo "TEST FAILED $i";
        fi
    done
fi

