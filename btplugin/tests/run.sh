#!/bin/bash
FAIL=0
TESTDIR=/Users/rjs/Code/pyangbind/btplugin/tests/
for i in `find $TESTDIR -mindepth 1 -maxdepth 1 -type d`; do
    #echo "TESTING $i..."
    $i/run.py > /dev/null
    if [ $? -ne 0 ]; then
        echo "TEST FAILED $i";
        FAIL = expr $FAIL + 1
    fi
done

if [ $FAIL -eq 0 ]; then
    echo "RESULT: all tests passed"
else
    echo "RESULT: $FAIL tests failed"
fi

