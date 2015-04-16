#!/bin/bash
TESTDIR=/Users/rjs/Code/pyangbind/btplugin/tests/
for i in `find $TESTDIR -mindepth 1 -maxdepth 1 -type d`; do
    echo "TESTING $i..."
    $i/run.py
    if [ $? -ne 0 ]; then
        echo "TEST FAILED $i";
    fi
done
