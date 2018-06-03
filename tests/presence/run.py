#!/usr/bin/env python

import json
import unittest

import pyangbind.lib.pybindJSON as pbJ
from pyangbind.lib.yangtypes import safe_name
from tests.base import PyangBindTestCase


class PresenceTests(PyangBindTestCase):
    yang_files = ["presence.yang"]
    pyang_flags = ["--use-extmethods", "--presence"]

    def setUp(self):
        self.instance = self.bindings.presence()

    def test_001_check_containers(self):
        for attr in ["empty-container", "parent", ["parent", "child"]]:
            with self.subTest(attr=attr):
                if isinstance(attr, list):
                    parent = self.instance
                    for v in attr:
                        parent = getattr(parent, v, None)
                        self.assertIsNot(parent, None)
                else:
                    elem = getattr(self.instance, safe_name(attr), None)
                    self.assertIsNot(elem, None)

    def test_002_check_presence(self):
        self.assertIs(self.instance.empty_container._presence, True)
        self.assertIs(self.instance.empty_container._cpresent, False)
        self.assertIs(self.instance.empty_container._present(), False)

    def test_003_check_set_present(self):
        smt = getattr(self.instance.empty_container, "_set_present", None)
        self.assertIsNot(smt, None)
        smt()
        self.assertIs(self.instance.empty_container._cpresent, True)
        self.assertIs(self.instance.empty_container._present(), True)

    def test_004_check_np(self):
        self.assertIs(self.instance.parent._presence, False)
        self.assertIs(self.instance.np_container._presence, False)
        self.assertIs(self.instance.np_container.s._presence, None)

    def test_005_check_hierarchy(self):
        self.assertIs(self.instance.pp._presence, True)
        self.assertIs(self.instance.pp._present(), False)
        self.assertIs(self.instance.pp._changed(), False)
        self.instance.pp.s = "teststring"
        self.assertIs(self.instance.pp._present(), True)
        self.assertIs(self.instance.pp._changed(), True)

    def test_006_check_invalid_hierarchy(self):
        self.assertIs(self.instance.parent._presence, False)
        self.assertIs(self.instance.parent.child._presence, True)
        self.assertIs(self.instance.parent.child._present(), False)
        self.instance.parent.child._set_present()
        self.assertIs(self.instance.parent.child._present(), True)
        self.assertIs(self.instance.parent._present(), None)

    def test_007_set_not_present(self):
        self.instance.parent.child._set_present()
        self.assertIs(self.instance.parent.child._present(), True)
        self.instance.parent.child._set_present(present=False)
        self.assertIs(self.instance.parent.child._present(), False)

    def test_008_presence_get(self):
        self.instance.parent.child._set_present()
        self.assertIs(self.instance.empty_container._present(), False)
        self.assertIs(self.instance.parent.child._present(), True)
        self.assertIs(self.instance.pp._present(), False)
        self.assertEqual(self.instance.get(filter=True), {"parent": {"child": {}}})

    def test_009_presence_serialise(self):
        self.instance.parent.child._set_present()
        expectedJ = """
                {
                    "parent": {
                        "child": {}
                    }
                }"""
        self.assertEqual(json.loads(pbJ.dumps(self.instance)), json.loads(expectedJ))

    def test_010_presence_deserialise(self):
        inputJ = """
              {
                "parent": {
                  "child": {}
                }
              }"""
        x = pbJ.loads(inputJ, self.bindings, "presence")
        self.assertIs(x.parent.child._present(), True)

    def test_011_presence_deserialise(self):
        inputJ = """
              {
                "presence:parent": {
                  "child": {}
                }
              }"""
        x = pbJ.loads_ietf(inputJ, self.bindings, "presence")
        self.assertIs(x.parent.child._present(), True)


if __name__ == "__main__":
    unittest.main()
