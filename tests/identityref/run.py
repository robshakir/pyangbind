#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class IdentityRefTests(PyangBindTestCase):
    yang_files = ["identityref.yang", "remote-two.yang"]

    def setUp(self):
        self.instance = self.bindings.identityref()

    def test_identityref_leafs_get_created(self):
        for leaf in ["id1", "idr1"]:
            with self.subTest(leaf=leaf):
                self.assertTrue(hasattr(self.instance.test_container, leaf))

    def test_cant_assign_invalid_string_to_identityref(self):
        with self.assertRaises(ValueError):
            self.instance.test_container.id1 = "hello"

    def test_identityref_leafs_are_blank_by_default(self):
        for leaf in ["id1", "idr1"]:
            with self.subTest(leaf=leaf):
                self.assertEqual(getattr(self.instance.test_container, leaf), "")

    def test_identityref_accepts_valid_identity_values(self):
        for identity in ["option-one", "option-two"]:
            with self.subTest(identity=identity):
                allowed = True
                try:
                    self.instance.test_container.id1 = identity
                except ValueError:
                    allowed = False
                self.assertTrue(allowed)

    def test_remote_identityref_accepts_valid_identity_values(self):
        for identity in ["remote-one", "remote-two"]:
            with self.subTest(identity=identity):
                allowed = True
                try:
                    self.instance.test_container.idr1 = identity
                except ValueError:
                    allowed = False
                self.assertTrue(allowed)

    def test_set_ancestral_identities_one(self):
        for (identity, valid) in [
            ("father", True),
            ("son", True),
            ("foo:father", True),
            ("foo:son", True),
            ("elephant", False),
            ("hamster", False),
        ]:
            with self.subTest(identity=identity, valid=valid):
                allowed = True
                try:
                    self.instance.test_container.id2 = identity
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_set_ancestral_identities_two(self):
        for (identity, valid) in [
            ("grandmother", True),
            ("mother", True),
            ("niece", False),
            ("aunt", True),
            ("cousin", True),
            ("daughter", True),
            ("son", False),
            ("father", False),
            ("grandfather", False),
        ]:
            with self.subTest(identity=identity, valid=valid):
                allowed = True
                try:
                    self.instance.test_container.id3 = identity
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_set_ancestral_identities_three(self):
        for (identity, valid) in [("daughter", True), ("cousin", False), ("aunt", False)]:
            with self.subTest(identity=identity, valid=valid):
                allowed = True
                try:
                    self.instance.test_container.id4 = identity
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_set_ancestral_identities_four(self):
        for (identity, valid) in [
            ("daughter", True),
            ("cousin", True),
            ("mother", True),
            ("aunt", True),
            ("greatgrandmother", False),
        ]:
            with self.subTest(identity=identity, valid=valid):
                allowed = True
                try:
                    self.instance.test_container.id5 = identity
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_grouping_identity_inheritance(self):
        for (address_type, valid) in [("source-dest", True), ("lcaf", True), ("unknown", False)]:
            with self.subTest(address_type=address_type, valid=valid):
                allowed = True
                try:
                    self.instance.ak.address_type = address_type
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_set_identityref_from_imported_module(self):
        for (identity, valid) in [
            ("remote:remote-one", True),
            ("fordprefect:remote-one", False),
            ("remote:remote-two", True),
        ]:
            with self.subTest(identity=identity, valid=valid):
                allowed = True
                try:
                    self.instance.test_container.idr1 = identity
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_set_identityref_from_imported_module_referencing_local(self):
        for (identity, valid) in [("remote-id", True), ("remote-two:remote-id", True), ("invalid", False)]:
            with self.subTest(identity=identity, valid=valid):
                allowed = True
                try:
                    self.instance.ietfint.ref = identity
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)


if __name__ == "__main__":
    unittest.main()
