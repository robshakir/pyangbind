#!/usr/bin/env python

import os.path
import unittest

from pyangbind.lib.xpathhelper import YANGPathHelper
from tests.base import PyangBindTestCase


class OpenconfigInterfacesTests(PyangBindTestCase):
    yang_files = [
        os.path.join("openconfig", "%s.yang" % fname)
        for fname in ["openconfig-interfaces", "openconfig-if-aggregate", "openconfig-if-ip"]
    ]
    pyang_flags = [
        "-p %s" % os.path.join(os.path.dirname(__file__), "include"),
        "--use-xpathhelper",
        "--lax-quote-checks",
    ]
    split_class_dir = True
    module_name = "ocbind"

    remote_yang_files = [
        {
            "local_path": "include",
            "remote_prefix": "https://raw.githubusercontent.com/robshakir/yang/master/standard/ietf/RFC/",
            "files": ["ietf-inet-types.yang", "ietf-yang-types.yang", "ietf-interfaces.yang"],
        },
        {
            "local_path": "include",
            "remote_prefix": "https://raw.githubusercontent.com/openconfig/public/master/release/models/",
            "files": [
                "openconfig-extensions.yang",
                "types/openconfig-types.yang",
                "vlan/openconfig-vlan.yang",
                "vlan/openconfig-vlan-types.yang",
                "types/openconfig-inet-types.yang",
                "types/openconfig-yang-types.yang",
            ],
        },
        {
            "local_path": "openconfig",
            "remote_prefix": "https://raw.githubusercontent.com/openconfig/public/master/release/models/",
            "files": [
                "interfaces/openconfig-if-ip.yang",
                "interfaces/openconfig-if-ethernet.yang",
                "interfaces/openconfig-if-aggregate.yang",
                "interfaces/openconfig-if-types.yang",
                "interfaces/openconfig-interfaces.yang",
            ],
        },
    ]

    def setUp(self):
        self.yang_helper = YANGPathHelper()
        self.instance = self.ocbind.openconfig_interfaces(path_helper=self.yang_helper)

    def test_001_populated_intf_type(self):
        i0 = self.instance.interfaces.interface.add("eth0")
        self.assertEqual(len(i0.config.type._restriction_dict), 1)


if __name__ == "__main__":
    unittest.main()
