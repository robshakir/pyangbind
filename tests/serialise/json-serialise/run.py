#!/usr/bin/env python

import json
import os.path
import unittest
from decimal import Decimal

import six
from bitarray import bitarray

from pyangbind.lib.pybindJSON import dumps
from pyangbind.lib.xpathhelper import YANGPathHelper
from tests.base import PyangBindTestCase


class JSONSerialiseTests(PyangBindTestCase):
    yang_files = ["json-serialise.yang"]
    pyang_flags = ["--use-xpathhelper"]

    def setUp(self):
        self.yang_helper = YANGPathHelper()
        self.serialise_obj = self.bindings.json_serialise(path_helper=self.yang_helper)

    def test_serialise_container(self):
        self.serialise_obj.two.string_test = "twenty-two"
        with open(os.path.join(os.path.dirname(__file__), "json", "container.json"), "r") as fp:
            self.assertEqual(
                json.loads(dumps(self.yang_helper.get("/two")[0])),
                json.load(fp),
                "Invalid output returned when serialising a container.",
            )

    def test_full_serialise(self):
        self.serialise_obj.c1.l1.add(1)
        for signed in ["int", "uint"]:
            for size in [8, 16, 32, 64]:
                name = "%s%s" % (signed, size)
                setter = getattr(self.serialise_obj.c1.l1[1], "_set_%s" % name)
                setter(1)
        self.serialise_obj.c1.l1[1].restricted_integer = 6
        self.serialise_obj.c1.l1[1].string = "bear"
        self.serialise_obj.c1.l1[1].restricted_string = "aardvark"
        self.serialise_obj.c1.l1[1].union = 16
        self.serialise_obj.c1.l1[1].union_list.append(16)
        self.serialise_obj.c1.l1[1].union_list.append("chicken")

        self.serialise_obj.c1.t1.add(16)
        self.serialise_obj.c1.t1.add(32)
        self.serialise_obj.c1.l1[1].leafref = 16

        self.serialise_obj.c1.l1[1].binary = bitarray("010101")
        self.serialise_obj.c1.l1[1].boolean = True
        self.serialise_obj.c1.l1[1].enumeration = "one"
        self.serialise_obj.c1.l1[1].identityref = "idone"
        self.serialise_obj.c1.l1[1].typedef_one = "test"
        self.serialise_obj.c1.l1[1].typedef_two = 8
        self.serialise_obj.c1.l1[1].one_leaf = "hi"
        for i in range(1, 5):
            self.serialise_obj.c1.l1[1].ll.append(six.text_type(i))
        self.serialise_obj.c1.l1[1].next_hop.append("DROP")
        self.serialise_obj.c1.l1[1].next_hop.append("192.0.2.1")
        self.serialise_obj.c1.l1[1].next_hop.append("fish")
        self.serialise_obj.c1.l1[1].typedef_decimal = Decimal("21.21")
        self.serialise_obj.c1.l1[1].range_decimal = Decimal("4.44443322")
        self.serialise_obj.c1.l1[1].typedef_decimalrange = Decimal("42.42")
        self.serialise_obj.c1.l1[1].decleaf = Decimal("42.4422")

        for i in range(1, 10):
            self.serialise_obj.c1.l2.add(i)

        pybind_json = json.loads(dumps(self.serialise_obj))
        with open(os.path.join(os.path.dirname(__file__), "json", "expected-output.json"), "r") as fp:
            external_json = json.load(fp)
        self.assertEqual(pybind_json, external_json, "JSON did not match expected output.")


if __name__ == "__main__":
    unittest.main()
