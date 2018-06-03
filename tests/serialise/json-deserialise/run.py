#!/usr/bin/env python
from __future__ import unicode_literals

import json
import os.path
import unittest
from bitarray import bitarray
from decimal import Decimal

import pyangbind.lib.pybindJSON as pbJ
import pyangbind.lib.serialise as pbS
from pyangbind.lib.serialise import pybindJSONDecoder
from pyangbind.lib.xpathhelper import YANGPathHelper

from tests.base import PyangBindTestCase


class JSONDeserialiseTests(PyangBindTestCase):
    yang_files = ["json-deserialise.yang"]
    maxDiff = None

    def setUp(self):
        self.yang_helper = YANGPathHelper()
        self.deserialise_obj = self.bindings.json_deserialise(path_helper=self.yang_helper)

    def test_load_full_object(self):
        expected_json = {
            "load-list": {
                "1": {"index": 1, "value": "one"},
                "3": {"index": 3, "value": "three"},
                "2": {"index": 2, "value": "two"},
            }
        }
        # For developers looking for examples, note that the arguments here are:
        #   - the file that we're trying to read
        #   - the bindings module that we generated
        #   - the name of the class within that module
        #   kwargs (path_helper, overwrite, etc.)
        actual_json = pbJ.load(
            os.path.join(os.path.dirname(__file__), "json", "list.json"),
            self.bindings,
            "json_deserialise",
            path_helper=self.yang_helper,
        ).get(filter=True)

        self.assertEqual(actual_json, expected_json, "Whole object load did not return the correct list.")

    def test_load_into_existing_object(self):
        with open(os.path.join(os.path.dirname(__file__), "json", "list-items.json"), "r") as fp:
            pbS.pybindJSONDecoder.load_json(json.load(fp), None, None, obj=self.deserialise_obj)
        expected_json = {"load-list": {"5": {"index": 5, "value": "five"}, "4": {"index": 4, "value": "four"}}}
        actual_json = self.deserialise_obj.get(filter=True)
        self.assertEqual(actual_json, expected_json, "Existing object load did not return the correct list.")

    def test_all_the_types(self):
        expected_json = {
            "c1": {
                "l1": {
                    "1": {
                        "one-leaf": "hi",
                        "typedef-one": "test",
                        "boolean": True,
                        "binary": bitarray("010101"),
                        "union": "16",
                        "identityref": "idone",
                        "enumeration": "one",
                        "k1": 1,
                        "uint16": 1,
                        "union-list": [16, "chicken"],
                        "uint32": 1,
                        "int32": 1,
                        "int16": 1,
                        "string": "bear",
                        "decimal": Decimal("42.42"),
                        "typedef-two": 8,
                        "uint8": 1,
                        "restricted-integer": 6,
                        "leafref": "16",
                        "int8": 1,
                        "uint64": 1,
                        "int64": 1,
                        "restricted-string": "aardvark",
                    }
                },
                "t1": {"32": {"target": "32"}, "16": {"target": "16"}},
            }
        }
        actual_json = pbJ.load(
            os.path.join(os.path.dirname(__file__), "json", "alltypes.json"),
            self.bindings,
            "json_deserialise",
            path_helper=self.yang_helper,
        ).get(filter=True)

        self.assertEqual(actual_json, expected_json, "Load of object with all items not correct.")

    def test_load_user_ordered_list(self):
        actual_json = pbJ.load(
            os.path.join(os.path.dirname(__file__), "json", "orderedlist-order.json"),
            self.bindings,
            "json_deserialise",
            path_helper=self.yang_helper,
        )
        self.assertEqual(list(actual_json.ordered.keys()), ["two", "one"])

    def test_load_json_ordered_list(self):
        actual_json = pbJ.load(
            os.path.join(os.path.dirname(__file__), "json", "orderedlist-no-order.json"),
            self.bindings,
            "json_deserialise",
            path_helper=self.yang_helper,
        )
        self.assertEqual(list(actual_json.ordered.keys()), ["two", "one"])

    def test_skip_unknown_keys(self):
        allowed = True
        try:
            with open(os.path.join(os.path.dirname(__file__), "json", "nonexist.json"), "r") as fp:
                pybindJSONDecoder.load_ietf_json(json.load(fp), self.bindings, "json_deserialise", skip_unknown=True)
        except AttributeError:
            allowed = False
        self.assertTrue(allowed, "Skipping keys that did not exist was not successfully handled.")

    def test_dont_skip_unknown_keys(self):
        allowed = True
        try:
            with open(os.path.join(os.path.dirname(__file__), "json", "nonexist.json"), "r") as fp:
                pybindJSONDecoder.load_ietf_json(json.load(fp), self.bindings, "json_deserialise", skip_unknown=False)
        except AttributeError:
            allowed = False
        self.assertFalse(allowed, "Skipping keys that did not exist was not successfully handled.")


if __name__ == "__main__":
    unittest.main()
