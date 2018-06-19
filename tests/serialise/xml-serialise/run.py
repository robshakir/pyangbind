#!/usr/bin/env python

import os.path
import unittest
from decimal import Decimal

import six
from bitarray import bitarray
from lxml import objectify

from pyangbind.lib.serialise import pybindIETFXMLEncoder
from pyangbind.lib.xpathhelper import YANGPathHelper
from tests.base import PyangBindTestCase


def xml_tree_equivalence(e1, e2):
    """
    Rough XML comparison function based on https://stackoverflow.com/a/24349916/1294458.
    This is necessary to provide some sort of structural equivalence of a generated XML
    tree; however there is no XML deserialisation implementation yet. A naive text comparison
    fails because it seems it enforces ordering, which seems to vary between python versions
    etc. Strictly speaking, I think, only the *leaf-list* element mandates ordering.. this
    function uses simple sorting on tag name, which I think, should maintain the relative
    order of these elements.
    """
    if e1.tag != e2.tag:
        return False
    if e1.text != e2.text:
        return False
    if e1.tail != e2.tail:
        return False
    if e1.attrib != e2.attrib:
        return False
    if len(e1) != len(e2):
        return False
    e1_children = sorted(e1.getchildren(), key=lambda x: x.tag)
    e2_children = sorted(e2.getchildren(), key=lambda x: x.tag)
    if len(e1_children) != len(e2_children):
        return False
    return all(xml_tree_equivalence(c1, c2) for c1, c2 in zip(e1_children, e2_children))


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

        self.serialise_obj.c1.l1[1].binary = bitarray("010101")
        self.serialise_obj.c1.l1[1].boolean = True
        self.serialise_obj.c1.l1[1].enumeration = "one"
        self.serialise_obj.c1.l1[1].identityref = "idone"
        self.serialise_obj.c1.l1[1].remote_identityref = "stilton"
        self.serialise_obj.c1.l1[1].typedef_one = "test"
        self.serialise_obj.c1.l1[1].typedef_two = 8
        self.serialise_obj.c1.l1[1].one_leaf = "hi"
        self.serialise_obj.c1.l1[1].uint64type = 2 ** 22
        self.serialise_obj.c1.l1[1].typedef_decimal = 32.29
        self.serialise_obj.c1.l1[1].typedef_decimalrange = Decimal("33.44")
        self.serialise_obj.c1.l1[1].range_decimal = Decimal("4.44443322")
        for i in range(1, 5):
            self.serialise_obj.c1.l1[1].ll.append(six.text_type(i))
        self.serialise_obj.c1.l1[1].next_hop.append("DROP")
        self.serialise_obj.c1.l1[1].next_hop.append("192.0.2.1")
        self.serialise_obj.c1.l1[1].next_hop.append("TEST")
        self.serialise_obj.augtarget.augleaf = "teststring"
        self.serialise_obj.c1.l1[1].decleaf = Decimal("42.4422")
        for i in range(1, 10):
            self.serialise_obj.c1.l2.add(i)

        doc = pybindIETFXMLEncoder().encode(self.serialise_obj)

        with open(os.path.join(os.path.dirname(__file__), "xml", "obj.xml"), "r") as fp:
            external_xml = fp.read()
            existing_doc = objectify.fromstring(external_xml)

        self.assertTrue(xml_tree_equivalence(doc, existing_doc), "Generated XML did not match the expected output.")


if __name__ == "__main__":
    unittest.main()
