#!/bin/bash
SDIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYBINDPLUGIN=`/usr/bin/env python -c 'import pyangbind; import os; print "%s/plugin" % os.path.dirname(pyangbind.__file__)'`
pyang --plugindir $PYBINDPLUGIN -f pybind --build-rpcs --split-class-dir $SDIR/rbindings simple_rpc.yang

echo "Bindings successfully generated!"
