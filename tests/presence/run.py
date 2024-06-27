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
        for attr in [
            "empty-container",
            "parent",
            ["parent", "child"],
            "np_container",
            "p_container",
            "p_container_grouping",
        ]:
            with self.subTest(attr=attr):
                if isinstance(attr, list):
                    parent = self.instance
                    for v in attr:
                        parent = getattr(parent, v, None)
                        self.assertIsNot(parent, None)
                else:
                    elem = getattr(self.instance, safe_name(attr), None)
                    self.assertIsNot(elem, None)

    def test_002_check_leafs(self):
        for attr in [
            ("np_container", "s"),
            ("p_container", "s"),
            ("p_container_grouping", "s"),
        ]:
            with self.subTest(attr=attr):
                container, leaf = attr
                cont_elem = getattr(self.instance, container, None)
                leaf_elem = getattr(cont_elem, leaf, None)
                self.assertIsNotNone(leaf_elem, "Missing leaf %s in container %s" % (leaf, container))

    def test_003_check_presence(self):
        self.assertIs(self.instance.empty_container._presence, True)
        self.assertIs(self.instance.empty_container._cpresent, False)
        self.assertIs(self.instance.empty_container._present(), False)

    def test_004_check_set_present(self):
        smt = getattr(self.instance.empty_container, "_set_present", None)
        self.assertIsNot(smt, None)
        smt()
        self.assertIs(self.instance.empty_container._cpresent, True)
        self.assertIs(self.instance.empty_container._present(), True)

    def test_005_check_np(self):
        self.assertIs(self.instance.parent._presence, False)
        self.assertIs(self.instance.np_container._presence, False)
        self.assertIs(self.instance.np_container.s._presence, None)

    def test_006_check_hierarchy(self):
        self.assertIs(self.instance.p_container._presence, True)
        self.assertIs(self.instance.p_container._present(), False)
        self.assertIs(self.instance.p_container._changed(), False)
        self.instance.p_container.s = "teststring"
        self.assertIs(self.instance.p_container._present(), True)
        self.assertIs(self.instance.p_container._changed(), True)

    def test_007_check_invalid_hierarchy(self):
        self.assertIs(self.instance.parent._presence, False)
        self.assertIs(self.instance.parent.child._presence, True)
        self.assertIs(self.instance.parent.child._present(), False)
        self.instance.parent.child._set_present()
        self.assertIs(self.instance.parent.child._present(), True)
        self.assertIs(self.instance.parent._present(), None)

    def test_008_set_not_present(self):
        self.instance.parent.child._set_present()
        self.assertIs(self.instance.parent.child._present(), True)
        self.instance.parent.child._set_present(present=False)
        self.assertIs(self.instance.parent.child._present(), False)

    def test_009_presence_get(self):
        self.instance.parent.child._set_present(True)
        self.assertIs(self.instance.empty_container._present(), False)
        self.assertIs(self.instance.parent.child._present(), True)
        self.assertIs(self.instance.p_container._present(), False)
        self.assertEqual(self.instance.get(filter=True), {"parent": {"child": {}}})
        self.instance.parent.child._set_present(False)
        self.assertIs(self.instance.parent.child._present(), False)
        self.assertEqual(self.instance.get(filter=True), {})

    def test_010_presence_serialise(self):
        self.instance.parent.child._set_present()
        self.instance.p_container._set_present()
        expectedJ = """
                {
                    "parent": {
                        "child": {}
                    },
                    "p-container": {}
                }"""
        self.assertEqual(json.loads(pbJ.dumps(self.instance)), json.loads(expectedJ))
        self.instance.parent.child._set_present(False)
        expectedJ = """
        {
            "p-container": {}
        }"""
        self.assertEqual(json.loads(pbJ.dumps(self.instance)), json.loads(expectedJ))

    def test_011_presence_serialise_ietf(self):
        self.instance.parent.child._set_present()
        self.instance.p_container._set_present()
        expectedJ = """
                {
                    "presence:parent": {
                        "child": {}
                    },
                    "presence:p-container": {}
                }"""
        self.assertEqual(json.loads(pbJ.dumps(self.instance, mode="ietf")), json.loads(expectedJ))
        self.instance.parent.child._set_present(False)
        expectedJ = """{"presence:p-container": {}}"""
        self.assertEqual(json.loads(pbJ.dumps(self.instance, mode="ietf")), json.loads(expectedJ))

    def test_012_presence_deserialise(self):
        inputJ = """
              {
                "parent": {
                  "child": {}
                },
                "p-container": {}
              }"""
        x = pbJ.loads(inputJ, self.bindings, "presence")
        self.assertIs(x.parent.child._present(), True)
        self.assertIs(x.p_container._present(), True)

    def test_013_presence_deserialise(self):
        inputJ = """
              {
                "presence:parent": {
                  "child": {}
                },
                "presence:p-container": {}
              }"""
        x = pbJ.loads_ietf(inputJ, self.bindings, "presence")
        self.assertIs(x.parent.child._present(), True)
        self.assertIs(x.p_container._present(), True)


class SplitClassesPresenceTests(PresenceTests):
    split_class_dir = True


if __name__ == "__main__":
    unittest.main()
