#!/usr/bin/env python

import os.path
import unittest
from decimal import Decimal

from lxml import objectify

from pyangbind.lib.serialise import pybindIETFXMLEncoder
from pyangbind.lib.xpathhelper import YANGPathHelper
from tests.base import PyangBindTestCase
from tests.serialise.xml_utils import xml_tree_equivalence


class XMLSerialiseTests(PyangBindTestCase):
    yang_files = ["ietf-xml-serialise.yang", "augment.yang"]
    maxDiff = None

    def setUp(self):
        self.yang_helper = YANGPathHelper()
        self.serialise_obj = self.bindings.ietf_xml_serialise(path_helper=self.yang_helper)

    def test_serialise_full_container(self):
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
        self.serialise_obj.c1.l1[1].empty = True

        self.serialise_obj.c1.t1.add(16)
        self.serialise_obj.c1.t1.add(32)
        self.serialise_obj.c1.l1[1].leafref = 16

        self.serialise_obj.c1.l1[1].binary = b"yang"
        self.serialise_obj.c1.l1[1].boolean = True
        self.serialise_obj.c1.l1[1].enumeration = "one"
        self.serialise_obj.c1.l1[1].identityref = "idone"
        self.serialise_obj.c1.l1[1].remote_identityref = "stilton"
        self.serialise_obj.c1.l1[1].typedef_one = "test"
        self.serialise_obj.c1.l1[1].typedef_two = 8
        self.serialise_obj.c1.l1[1].one_leaf = "hi"
        self.serialise_obj.c1.l1[1].uint64type = 2**22
        self.serialise_obj.c1.l1[1].typedef_decimal = 32.29
        self.serialise_obj.c1.l1[1].typedef_decimalrange = Decimal("33.44")
        self.serialise_obj.c1.l1[1].range_decimal = Decimal("4.44443322")
        for i in range(1, 5):
            self.serialise_obj.c1.l1[1].ll.append(str(i))
        self.serialise_obj.c1.l1[1].next_hop.append("DROP")
        self.serialise_obj.c1.l1[1].next_hop.append("192.0.2.1")
        self.serialise_obj.c1.l1[1].next_hop.append("TEST")
        self.serialise_obj.augtarget.augleaf = "teststring"
        self.serialise_obj.c1.l1[1].decleaf = Decimal("42.4422")
        self.serialise_obj.c1.l1[1].typedefed_bits = "bit1 bit2"
        self.serialise_obj.c1.l1[1].leaf_bits = "b1 b3"
        for i in range(1, 10):
            self.serialise_obj.c1.l2.add(i)

        doc = pybindIETFXMLEncoder().encode(self.serialise_obj)

        with open(os.path.join(os.path.dirname(__file__), "xml", "obj.xml"), "r") as fp:
            external_xml = fp.read()
            existing_doc = objectify.fromstring(external_xml)

        self.assertTrue(xml_tree_equivalence(doc, existing_doc), "Generated XML did not match the expected output.")


if __name__ == "__main__":
    unittest.main()
