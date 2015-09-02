#!/bin/bash

TESTDIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
$TESTDIR/yang_tests.sh
$TESTDIR/xpath/xpath_tests.sh
$TESTDIR/serialise/serialise_tests.sh

