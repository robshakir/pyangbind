#!/usr/bin/env python

import json
import os
import unittest

import pyangbind.lib.pybindJSON as pbJ
from pyangbind.lib.serialise import pybindJSONDecoder
from pyangbind.lib.xpathhelper import YANGPathHelper
from pyangbind.lib.yangtypes import safe_name
from tests.base import PyangBindTestCase


class XPathRootTests(PyangBindTestCase):
    yang_files = ["root-tc04-a.yang", "root-tc04-b.yang"]
    pyang_flags = ["--use-extmethods", "--use-xpathhelper"]

    def setUp(self):
        self.path_helper = YANGPathHelper()
        self.instance_a = self.bindings.root_tc04_a(path_helper=self.path_helper)
        self.instance_b = self.bindings.root_tc04_b(path_helper=self.path_helper)

    def test_001_check_containers(self):
        self.assertIsNot(getattr(self.instance_a, safe_name("root-tc04-a"), None), None)
        self.assertIsNot(getattr(self.instance_b, safe_name("root-tc04-b"), None), None)

    def test_002_base_gets(self):
        # each of these raise exceptions so will cause test case failures
        self.path_helper.get_unique("/")
        self.path_helper.get_unique("/root-tc04-a")
        self.path_helper.get_unique("/root-tc04-b")

    def test_003_base_sets(self):
        a = self.path_helper.get_unique("/root-tc04-a")
        a.a = "little-cottonwood"
        self.assertEqual(self.instance_a.root_tc04_a.a, "little-cottonwood")
        b = self.path_helper.get_unique("/root-tc04-b")
        b.b = "big-cottonwood"
        self.assertEqual(self.instance_b.root_tc04_b.b, "big-cottonwood")

    def test_004_serialise(self):
        self.instance_a.root_tc04_a.a = "emigration"
        self.instance_b.root_tc04_b.b = "alpine-fork"
        with open(os.path.join(os.path.dirname(__file__), "json", "04-serialise.json")) as fp:
            expected_json = json.load(fp)
        v = json.loads(pbJ.dumps(self.path_helper.get_unique("/")))
        self.assertEqual(v, expected_json)

        with open(os.path.join(os.path.dirname(__file__), "json", "04b-ietf-serialise.json")) as fp:
            expected_ietf_json = json.load(fp)
        v = json.loads(pbJ.dumps(self.path_helper.get_unique("/"), mode="ietf"))
        self.assertEqual(v, expected_ietf_json)

    def test_005_deserialise(self):
        root = self.path_helper.get_unique("/")
        with open(os.path.join(os.path.dirname(__file__), "json", "05-deserialise.json"), "r") as fp:
            pybindJSONDecoder.load_json(json.load(fp), None, None, obj=root)
        v = json.loads(pbJ.dumps(self.path_helper.get_unique("/")))
        with open(os.path.join(os.path.dirname(__file__), "json", "05-deserialise.json"), "r") as fp:
            x = json.load(fp)
        self.assertEqual(v, x)

    def test_006_ietf_deserialise(self):
        root = self.path_helper.get_unique("/")
        with open(os.path.join(os.path.dirname(__file__), "json", "06-deserialise-ietf.json"), "r") as fp:
            pybindJSONDecoder.load_ietf_json(json.load(fp), None, None, obj=root)
        v = json.loads(pbJ.dumps(self.path_helper.get_unique("/"), mode="ietf"))
        with open(os.path.join(os.path.dirname(__file__), "json", "06-deserialise-ietf.json"), "r") as fp:
            x = json.load(fp)
        self.assertEqual(v, x)


if __name__ == "__main__":
    unittest.main()
