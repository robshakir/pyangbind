#!/bin/bash
SDIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
curl https://raw.githubusercontent.com/openconfig/public/master/release/models/local-routing/openconfig-local-routing.yang -o $SDIR/yang/openconfig-local-routing.yang
curl https://raw.githubusercontent.com/openconfig/public/master/release/models/interfaces/openconfig-interfaces.yang -o $SDIR/yang/openconfig-interfaces.yang
curl https://raw.githubusercontent.com/openconfig/public/master/release/models/openconfig-extensions.yang -o $SDIR/yang/openconfig-extensions.yang
curl https://raw.githubusercontent.com/openconfig/public/master/release/models/policy/openconfig-policy-types.yang -o $SDIR/yang/openconfig-policy-types.yang
curl https://raw.githubusercontent.com/robshakir/yang/master/standard/ietf/RFC/ietf-yang-types.yang -o $SDIR/yang/ietf-yang-types.yang
curl https://raw.githubusercontent.com/robshakir/yang/master/standard/ietf/RFC/ietf-inet-types.yang -o $SDIR/yang/ietf-inet-types.yang
curl https://raw.githubusercontent.com/robshakir/yang/master/standard/ietf/RFC/ietf-interfaces.yang -o $SDIR/yang/ietf-interfaces.yang
curl https://raw.githubusercontent.com/openconfig/public/master/release/models/types/openconfig-inet-types.yang -o $SDIR/yang/openconfig-inet-types.yang
curl https://raw.githubusercontent.com/openconfig/public/master/release/models/types/openconfig-yang-types.yang -o $SDIR/yang/openconfig-yang-types.yang
curl https://raw.githubusercontent.com/openconfig/public/master/release/models/types/openconfig-types.yang -o $SDIR/yang/openconfig-types.yang

PYBINDPLUGIN=`/usr/bin/env python -c 'import pyangbind; import os; print ("{}/plugin".format(os.path.dirname(pyangbind.__file__)))'`
pyang --plugindir $PYBINDPLUGIN -f pybind -p $SDIR/yang/ -o $SDIR/binding.py $SDIR/yang/openconfig-local-routing.yang

echo "Bindings successfully generated!"
