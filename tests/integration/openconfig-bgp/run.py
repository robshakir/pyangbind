#!/usr/bin/env python

import json
import os.path
import unittest

import pyangbind.lib.pybindJSON as pbj
from pyangbind.lib.xpathhelper import YANGPathHelper
from tests.base import PyangBindTestCase


class OpenconfigBGPTests(PyangBindTestCase):
    yang_files = [os.path.join("openconfig", "openconfig-bgp.yang")]
    pyang_flags = ["-p %s" % os.path.join(os.path.dirname(__file__), "include"), "--use-xpathhelper"]
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
                "policy/openconfig-policy-types.yang",
                "openconfig-extensions.yang",
                "types/openconfig-types.yang",
                "types/openconfig-inet-types.yang",
                "types/openconfig-yang-types.yang",
            ],
        },
        {
            "local_path": "openconfig",
            "remote_prefix": "https://raw.githubusercontent.com/openconfig/public/master/release/models/",
            "files": [
                "policy/openconfig-routing-policy.yang",
                "bgp/openconfig-bgp-common-multiprotocol.yang",
                "bgp/openconfig-bgp-common-structure.yang",
                "bgp/openconfig-bgp-common.yang",
                "bgp/openconfig-bgp-global.yang",
                "bgp/openconfig-bgp-neighbor.yang",
                "bgp/openconfig-bgp-peer-group.yang",
                "bgp/openconfig-bgp-policy.yang",
                "bgp/openconfig-bgp-types.yang",
                "bgp/openconfig-bgp.yang",
                "bgp/openconfig-bgp-errors.yang",
                "interfaces/openconfig-interfaces.yang",
            ],
        },
    ]

    def setUp(self):
        self.yang_helper = YANGPathHelper()
        self.instance = self.ocbind.openconfig_bgp(path_helper=self.yang_helper)

    def test_001_add_bgp_neighbor(self):
        self.instance.bgp.neighbors.neighbor.add("192.0.2.1")
        self.assertEqual(len(self.instance.bgp.neighbors.neighbor), 1)

    def test_010_filtered_json_output(self):
        self.instance.bgp.global_.config.as_ = 2856
        self.instance.bgp.global_.config.router_id = "192.0.2.1"
        n = self.instance.bgp.neighbors.neighbor.add("192.1.1.1")
        n.config.peer_as = 5400
        n.config.description = "a fictional transit session"
        json_out = pbj.dumps(self.instance)
        with open(os.path.join(os.path.dirname(__file__), "testdata", "tc010.json")) as fp:
            testdata = fp.read()
        self.assertEqual(json.loads(json_out), json.loads(testdata))

    def test_020_unfiltered_json_output(self):
        self.instance.bgp.global_.config.as_ = 2856
        self.instance.bgp.global_.config.router_id = "192.0.2.1"
        n = self.instance.bgp.neighbors.neighbor.add("192.1.1.1")
        n.config.peer_as = 5400
        n.config.description = "a fictional transit session"
        json_out = pbj.dumps(self.instance, filter=False)
        with open(os.path.join(os.path.dirname(__file__), "testdata", "tc020.json")) as fp:
            testdata = fp.read()
        self.assertEqual(json.loads(json_out), json.loads(testdata))

    def test_030_filtered_ietf_json_output(self):
        self.instance.bgp.global_.config.as_ = 2856
        self.instance.bgp.global_.config.router_id = "192.0.2.1"
        n = self.instance.bgp.neighbors.neighbor.add("192.1.1.1")
        n.config.peer_as = 5400
        n.config.description = "a fictional transit session"
        json_out = pbj.dumps(self.instance, mode="ietf")
        with open(os.path.join(os.path.dirname(__file__), "testdata", "tc030.json")) as fp:
            testdata = fp.read()
        self.assertEqual(json.loads(json_out), json.loads(testdata))

    def test_040_unfiltered_ietf_json_output(self):
        self.instance.bgp.global_.config.as_ = 2856
        self.instance.bgp.global_.config.router_id = "192.0.2.1"
        n = self.instance.bgp.neighbors.neighbor.add("192.1.1.1")
        n.config.peer_as = 5400
        n.config.description = "a fictional transit session"
        json_out = pbj.dumps(self.instance, filter=False, mode="ietf")
        with open(os.path.join(os.path.dirname(__file__), "testdata", "tc040.json")) as fp:
            testdata = fp.read()
        self.assertEqual(json.loads(json_out), json.loads(testdata))


if __name__ == "__main__":
    unittest.main()
