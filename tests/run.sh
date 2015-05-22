#!/bin/bash
FAIL=0
TESTDIR=/Users/rjs/Code/pyangbind/btplugin/tests/
PLUGINDIR=/Users/rjs/Code/pyangbind/btplugin

echo "RUNNING BASE"
/usr/local/bin/pyang --plugindir $PLUGINDIR -f bt $TESTDIR/base-test.yang -o /tmp/chkplugin.pyang >/dev/null
if [ $? -ne 0 ]; then
	echo "RESULT: CANNOT RUN TESTS, BROKEN PLUGIN"
	exit
fi
rm /tmp/chkplugin.pyang

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

