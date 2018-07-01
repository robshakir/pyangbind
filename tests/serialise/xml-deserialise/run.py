#!/usr/bin/env python

import os.path
import unittest

from lxml import objectify

from pyangbind.lib.serialise import pybindIETFXMLDecoder, pybindIETFXMLEncoder
from tests.base import PyangBindTestCase
from tests.serialise.xml_utils import xml_tree_equivalence


class XMLDeserialiseTests(PyangBindTestCase):
    yang_files = ["ietf-xml-deserialise.yang", "augment.yang"]
    maxDiff = None

    def test_deserialise_full_container_roundtrip(self):
        with open(os.path.join(os.path.dirname(__file__), "xml", "obj.xml"), "r") as fp:
            external_xml = fp.read()
            existing_doc = objectify.fromstring(external_xml)

        result = pybindIETFXMLDecoder().decode(external_xml, self.bindings, "ietf_xml_deserialise")
        doc = pybindIETFXMLEncoder().encode(result)

        self.assertTrue(xml_tree_equivalence(doc, existing_doc), "Generated XML did not match the expected output.")


if __name__ == "__main__":
    unittest.main()
