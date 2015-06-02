#!/bin/bash
# set to true or false
DEL=true
FAIL=0
TESTDIR=`pwd`
export PYANGBINDPATH=$TESTDIR/..
export PYANGPATH=`which pyang`
export XPATHLIBDIR=$TESTDIR/../lib/

echo "RUNNING BASE"
ln -s $XPATHLIBDIR/xpathhelper.py $TESTDIR/xpathhelper.py
$PYANGPATH --plugindir $PYANGBINDPATH -f pybind $TESTDIR/base-test.yang -o /tmp/chkplugin.pyang >/dev/null
if [ $? -ne 0 ]; then
    echo "RESULT: CANNOT RUN TESTS, BROKEN PLUGIN"
    exit
fi
rm /tmp/chkplugin.pyang
rm $TESTDIR/xpathhelper.py

if [ $# -eq 0 ]; then
    FAIL=0
    for i in `find $TESTDIR -mindepth 1 -maxdepth 1 -type d`; do
        echo "TESTING $i..."
        ln -s $XPATHLIBDIR/xpathhelper.py $i/xpathhelper.py
        if [ "$DEL" = true ]; then
            $i/run.py > /dev/null
        else
            $i/run.py -k > /dev/null
        fi
        if [ $? -ne 0 ]; then
            echo "TEST FAILED $i";
            FAIL=$((FAIL+1))
        fi
        rm $i/xpathhelper.py
    done
    if [ $FAIL -eq 0 ]; then
        echo "RESULT: all tests passed"
    else
        echo "RESULT: $FAIL tests failed"
    fi
else
    for i in "$@"; do
        echo "TESTING $i..."
        ln -s $XPATHLIBDIR/xpathhelper.py $i/xpathhelper.py
        if [ "$DEL" = true ]; then
            $i/run.py > /dev/null
        else
            $i/run.py -k > /dev/null
        fi
        if [ $? -ne 0 ]; then
            echo "TEST FAILED $i";
        fi
        rm $i/xpathhelper.py
    done
fi

