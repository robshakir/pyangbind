#!/bin/bash
SDIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DDIR=$SDIR/models
mkdir $DDIR

git clone https://github.com/openconfig/public $DDIR
export PYBINDPLUGIN=`/usr/bin/env python3 -c 'import pyangbind; import os; print ("{}/plugin".format(os.path.dirname(pyangbind.__file__)))'`
pyang --plugindir $PYBINDPLUGIN -f pybind -o binding.py docs/example/oc-network-instance/models/release/models/network-instance/openconfig-network-instance.yang -p ./docs/example/oc-network-instance/models/release/models/

echo "bindings.py successfully generated on current directory!"
