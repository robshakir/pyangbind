#!/usr/bin/env python

import json
import unittest

from pyangbind.lib import pybindJSON
from pyangbind.lib.serialise import pybindJSONDecoder
from tests.base import PyangBindTestCase


class IdentityRefTests(PyangBindTestCase):
    yang_files = ["identityref.yang", "remote-two.yang"]

    def setUp(self):
        self.instance = self.bindings.identityref()

    def test_identityref_leafs_get_created(self):
        for leaf in ["id_base", "id_remote"]:
            with self.subTest(leaf=leaf):
                self.assertTrue(hasattr(self.instance.test_container, leaf))

    def test_cant_assign_invalid_string_to_identityref(self):
        with self.assertRaises(ValueError):
            self.instance.test_container.grandfather = "hello"

    def test_identityref_leafs_are_blank_by_default(self):
        for leaf in ["id_base", "id_remote"]:
            with self.subTest(leaf=leaf):
                self.assertEqual(getattr(self.instance.test_container, leaf), "")

    def test_identityref_accepts_valid_identity_values(self):
        for identity in ["option-one", "option-two"]:
            with self.subTest(identity=identity):
                allowed = True
                try:
                    self.instance.test_container.id_base = identity
                except ValueError:
                    allowed = False
                self.assertTrue(allowed)

    def test_remote_identityref_accepts_valid_identity_values(self):
        for identity in ["remote-one", "remote-two"]:
            with self.subTest(identity=identity):
                allowed = True
                try:
                    self.instance.test_container.id_remote = identity
                except ValueError:
                    allowed = False
                self.assertTrue(allowed)

    def test_set_ancestral_identities_one(self):
        for identity, valid in [
            ("father", True),
            ("son", True),
            ("daughter", True),
            ("mother", False),
            ("foo:father", True),
            ("foo:son", True),
            ("elephant", False),
            ("hamster", False),
        ]:
            with self.subTest(identity=identity, valid=valid):
                allowed = True
                try:
                    self.instance.test_container.grandfather = identity
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid, identity)

    def test_set_ancestral_identities_two(self):
        for identity, valid in [
            ("grandmother", True),
            ("mother", True),
            ("niece", False),
            ("aunt", True),
            ("cousin", True),
            ("daughter", True),
            ("son", True),
            ("father", False),
            ("grandfather", False),
        ]:
            with self.subTest(identity=identity, valid=valid):
                allowed = True
                try:
                    self.instance.test_container.greatgrandmother = identity
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid, identity)

    def test_set_ancestral_identities_three(self):
        for identity, valid in [("daughter", True), ("son", True), ("cousin", False), ("aunt", False)]:
            with self.subTest(identity=identity, valid=valid):
                allowed = True
                try:
                    self.instance.test_container.mother = identity
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid, identity)

    def test_set_ancestral_identities_four(self):
        for identity, valid in [
            ("daughter", True),
            ("son", True),
            ("cousin", True),
            ("mother", True),
            ("father", False),
            ("aunt", True),
            ("greatgrandmother", False),
        ]:
            with self.subTest(identity=identity, valid=valid):
                allowed = True
                try:
                    self.instance.test_container.grandmother = identity
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid, identity)

    def test_set_ancestral_identities_five(self):
        for identity, valid in [
            ("mother", False),
            ("father", True),
            ("cousin", False),
            ("son", True),
        ]:
            with self.subTest(identity=identity, valid=valid):
                allowed = True
                try:
                    self.instance.test_container.grandparent = identity
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid, identity)

    def test_grouping_identity_inheritance(self):
        for address_type, valid in [
            ("source-dest", True),
            ("lcaf", True),
            ("unknown", False),
            ("identityref:source-dest", True),
        ]:
            with self.subTest(address_type=address_type, valid=valid):
                allowed = True
                try:
                    self.instance.ak.address_type = address_type
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_set_identityref_from_imported_module(self):
        for identity, valid in [
            ("remote:remote-one", True),
            ("fordprefect:remote-one", False),
            ("remote:remote-two", True),
        ]:
            with self.subTest(identity=identity, valid=valid):
                allowed = True
                try:
                    self.instance.test_container.id_remote = identity
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_set_identityref_from_imported_module_referencing_local(self):
        for identity, valid in [("remote-id", True), ("remote-two:remote-id", True), ("invalid", False)]:
            with self.subTest(identity=identity, valid=valid):
                allowed = True
                try:
                    self.instance.ietfint.ref = identity
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_json_ietf_serialise_namespace_handling_remote(self):
        for identity in ["remote-id", "remote-two:remote-id"]:
            with self.subTest(identity=identity):
                self.instance.ietfint.ref = identity
                data = json.loads(pybindJSON.dumps(self.instance, mode="ietf"))
                # The JSON representation of the identityref must have a namespace, as
                # the leaf `ref` and the identity `remote-id` are defined in two separate
                # modules
                self.assertEqual(
                    data["identityref:ietfint"]["ref"],
                    "remote-two:remote-id",
                )

    def test_json_ietf_serialise_namespace_handling_local(self):
        for identity in ["lcaf", "identityref:lcaf"]:
            with self.subTest(identity=identity):
                self.instance.ak.address_type = "lcaf"
                data = json.loads(pybindJSON.dumps(self.instance, mode="ietf"))
                # The JSON representation of the identityref may have, or may omit,
                # the namespace, as the leaf `address-type` and the identity `lcaf` are
                # defined in the same module, so accept either form
                self.assertIn(
                    data["identityref:ak"]["address-type"],
                    ["lcaf", "identityref:lcaf"],
                )

    def test_load_identityref_with_module_prefix(self):
        json = {
            "identityref:ak": {
                "address-type": "identityref:source-dest",
            }
        }
        obj = pybindJSONDecoder.load_ietf_json(json, self.bindings, "identityref")
        self.assertIn(
            obj.ak.address_type,
            ["identityref:source-dest", "source-dest"],
        )


if __name__ == "__main__":
    unittest.main()
