#!/bin/bash
SDIR="$(cd -P "$(dirname "$[0]")" && pwd)"
DDIR=$SDIR/models
mkdir $DDIR

git clone https://github.com/openconfig/public $DDIR
export PYBINDPLUGIN=`/usr/bin/env python3 -c 'import pyangbind; import os; print ("{}/plugin".format(os.path.dirname(pyangbind.__file__)))'`
pyang --plugindir $PYBINDPLUGIN -f pybind -o $SDIR/binding.py -p $DDIR/ $DDIR/release/models/network-instance/openconfig-network-instance.yang
echo "bindings.py successfully generated on current directory!"
rm -rf $DDIR
