#!/bin/bash
# set to true or false
DEL=false
FAIL=0

TESTDIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYANGBINDPATH=$TESTDIR/../..
export PYANGPATH=`which pyang`
export XPATHLIBDIR=$TESTDIR/../../lib/

if [ $# -eq 0 ]; then
    FAIL=0
    for i in `find $TESTDIR -mindepth 1 -maxdepth 1 -type d`; do
        if [ -e $i/run.py ]; then
            echo "TESTING $i..."
            if [ "$DEL" = true ]; then
                $i/run.py > /dev/null
            else
                $i/run.py -k > /dev/null
            fi
            if [ $? -ne 0 ]; then
                echo "TEST FAILED $i";
                FAIL=$((FAIL+1))
            fi
        fi
    done
    if [ $FAIL -eq 0 ]; then
        echo "RESULT: all tests passed"
    else
        echo "RESULT: $FAIL tests failed"
    fi
else
    for i in "$@"; do
        if [ -e $i/run.py ]; then
            echo "TESTING $i..."
            if [ "$DEL" = true ]; then
                $i/run.py
                #> /dev/null
            else
                $i/run.py -k
                #> /dev/null
            fi
            if [ $? -ne 0 ]; then
                echo "TEST FAILED $i";
            fi
        fi
    done
fi

