#!/usr/bin/env python

import os.path
import unittest

from pyangbind.lib.serialise import pybindIETFXMLDecoder, pybindIETFXMLEncoder
from tests.base import PyangBindTestCase


class XMLDeserialiseTests(PyangBindTestCase):
    yang_files = ["ietf-xml-deserialise.yang", "augment.yang"]
    maxDiff = None

    def test_deserialise_full_container_roundtrip(self):
        with open(os.path.join(os.path.dirname(__file__), "xml", "obj.xml"), "r") as fp:
            external_xml = fp.read()

        result = pybindIETFXMLDecoder().decode(external_xml, self.bindings, "ietf_xml_deserialise")
        result_xml = pybindIETFXMLEncoder().serialise(result)

        self.assertEqual(external_xml, result_xml)


if __name__ == "__main__":
    unittest.main()
