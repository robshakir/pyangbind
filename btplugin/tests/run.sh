#!/bin/bash
TESTDIR=/Users/rjs/Code/pyangbind/btplugin/tests/
for i in `find $TESTDIR -maxdepth 1 -type d`; do
    $i/run.py
    if [ $? -ne 0 ]; then
        echo "TEST FAILED $i";
    fi
done
