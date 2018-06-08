#!/usr/bin/env python
from __future__ import unicode_literals

import json
import os.path
import unittest
from collections import OrderedDict
from decimal import Decimal

from bitarray import bitarray

from pyangbind.lib.serialise import pybindJSONDecoder
from tests.base import PyangBindTestCase


class IETFJSONDeserialiseTests(PyangBindTestCase):
    yang_files = ["ietf-json-deserialise.yang"]
    maxDiff = None

    def test_multi_key_list_load(self):
        expected_json = {
            "mkey": {"one 1": {"leaf-two": 1, "leaf-one": "one"}, "three 2": {"leaf-two": 2, "leaf-one": "three"}}
        }
        with open(os.path.join(os.path.dirname(__file__), "json", "mkeylist.json")) as fp:
            actual_json = pybindJSONDecoder.load_ietf_json(json.load(fp), self.bindings, "ietf_json_deserialise").get(
                filter=True
            )
        self.assertEqual(actual_json, expected_json, "Multikey list load did not return expected JSON")

    def test_single_key_list_load(self):
        expected_json = {
            "skey": {"one": {"leaf-one": "one"}, "three": {"leaf-one": "three"}, "two": {"leaf-one": "two"}}
        }
        with open(os.path.join(os.path.dirname(__file__), "json", "skeylist.json")) as fp:
            actual_json = pybindJSONDecoder.load_ietf_json(json.load(fp), self.bindings, "ietf_json_deserialise").get(
                filter=True
            )
        self.assertEqual(actual_json, expected_json, "Single key list load did not return expected JSON")

    def test_list_with_children_load(self):
        expected_json = {
            "chlist": {
                1: {"keyleaf": 1, "child": {"number": 1, "string": "one"}},
                2: {"keyleaf": 2, "child": {"number": 2, "string": "two"}},
            }
        }
        with open(os.path.join(os.path.dirname(__file__), "json", "chlist.json")) as fp:
            actual_json = pybindJSONDecoder.load_ietf_json(json.load(fp), self.bindings, "ietf_json_deserialise").get(
                filter=True
            )
        self.assertEqual(actual_json, expected_json, "List with children load did not return expected JSON")

    def test_all_the_types(self):
        expected_json = {
            "c1": {
                "l1": {
                    1: {
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
                        "typedef-two": 8,
                        "uint8": 1,
                        "restricted-integer": 6,
                        "leafref": "16",
                        "int8": 1,
                        "uint64": 1,
                        "remote-identityref": "stilton",
                        "int64": 1,
                        "restricted-string": "aardvark",
                        "decimal": Decimal("16.32"),
                        "empty": True,
                    }
                },
                "l2": OrderedDict(
                    [
                        (1, {"k1": 1}),
                        (2, {"k1": 2}),
                        (3, {"k1": 3}),
                        (4, {"k1": 4}),
                        (5, {"k1": 5}),
                        (6, {"k1": 6}),
                        (7, {"k1": 7}),
                        (8, {"k1": 8}),
                        (9, {"k1": 9}),
                    ]
                ),
                "t1": {"32": {"target": "32"}, "16": {"target": "16"}},
            }
        }
        with open(os.path.join(os.path.dirname(__file__), "json", "complete-obj.json")) as fp:
            actual_json = pybindJSONDecoder.load_ietf_json(json.load(fp), self.bindings, "ietf_json_deserialise").get(
                filter=True
            )
        self.assertEqual(actual_json, expected_json, "Deserialisation of complete object not as expected.")

    def test_skip_unknown_keys(self):
        allowed = True
        try:
            with open(os.path.join(os.path.dirname(__file__), "json", "nonexistkey.json")) as fp:
                pybindJSONDecoder.load_ietf_json(
                    json.load(fp), self.bindings, "ietf_json_deserialise", skip_unknown=True
                )
        except AttributeError:
            allowed = False
        self.assertTrue(allowed, "Skipping keys that did not exist was not successfully handled.")

    def test_dont_skip_unknown_keys(self):
        allowed = True
        try:
            with open(os.path.join(os.path.dirname(__file__), "json", "nonexistkey.json")) as fp:
                pybindJSONDecoder.load_ietf_json(
                    json.load(fp), self.bindings, "ietf_json_deserialise", skip_unknown=False
                )
        except AttributeError:
            allowed = False
        self.assertFalse(allowed, "Skipping keys that did not exist was not successfully handled.")


if __name__ == "__main__":
    unittest.main()
