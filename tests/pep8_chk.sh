#!/bin/bash

TESTDIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for path in pyangbind tests; do
    for f in `find $TESTDIR/../$path -name "*.py" | grep -v "pyvirtualenv"`; do
        PEP8ERROR=`pep8 $f |egrep -v "E(111|114|127|128)"`
        if [[ ! -z $PEP8ERROR ]]; then
          echo "$PEP8ERROR" > $f.PEP8-ERRORS;
        fi
    done
done


