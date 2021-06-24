#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class BinaryTests(PyangBindTestCase):
    yang_files = ["binary.yang"]

    def setUp(self):
        self.binary_obj = self.bindings.binary()

    def test_binary_leafs_exist(self):
        for leaf in ["b1", "b2", "b3"]:
            with self.subTest(leaf=leaf):
                self.assertTrue(
                    hasattr(self.binary_obj.container, leaf), "Element did not exist in container (%s)" % leaf
                )

    def test_set_binary_from_different_datatypes(self):
        for value in [(b"42", True), ({"42": 42}, False), (-42, False), ("Arthur Dent", False)]:
            with self.subTest(value=value):
                allowed = True
                try:
                    self.binary_obj.container.b1 = value[0]
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, value[1], "Could incorrectly set b1 to %s" % value[0])

    def test_binary_leaf_default_value(self):
        default = b"yang"
        self.assertEqual(
            self.binary_obj.container.b2._default,
            default,
            "Default for leaf b2 was not set correctly (%s != %s)" % (self.binary_obj.container.b2._default, default),
        )

    def test_binary_leaf_is_empty_by_default(self):
        empty = b""
        self.assertEqual(
            self.binary_obj.container.b2,
            empty,
            "Value of binary leaf was not null when checking b2 (%s != %s)" % (self.binary_obj.container.b2, empty),
        )

    def test_binary_leaf_is_not_changed_by_default(self):
        self.assertFalse(
            self.binary_obj.container.b2._changed(),
            "Unset binary leaf specified changed when was default (%s != False)"
            % self.binary_obj.container.b2._changed(),
        )

    def test_set_binary_stores_value(self):
        bits = b"010"
        self.binary_obj.container.b2 = bits
        self.assertEqual(
            self.binary_obj.container.b2,
            bits,
            "Binary leaf not successfully set (%s != %s)" % (self.binary_obj.container.b2, bits),
        )

    def test_setting_binary_set_changed(self):
        self.binary_obj.container.b2 = b"010"
        self.assertTrue(
            self.binary_obj.container.b2._changed(),
            "Binary leaf value not flagged as changed (%s != True)" % self.binary_obj.container.b2._changed(),
        )

    def test_set_specific_length_binary_leaf(self):
        for bits in [(b"1", False), (b"12", True), (b"1234", False)]:
            with self.subTest(bits=bits):
                allowed = True
                try:
                    self.binary_obj.container.b3 = bits[0]
                except ValueError:
                    allowed = False
                self.assertEqual(
                    allowed,
                    bits[1],
                    "limited length binary incorrectly set to %s (%s != %s)" % (bits[0], bits[1], allowed),
                )

    def test_set_binary_leaf_with_length_range(self):
        for bits in [(b"1", False), (b"12", True), (b"1234", True), (b"12345", False)]:
            with self.subTest(bits=bits):
                allowed = True
                try:
                    self.binary_obj.container.b4 = bits[0]
                except ValueError:
                    allowed = False
                self.assertEqual(
                    allowed,
                    bits[1],
                    "Limited length binary with range incorrectly set to %s (%s != %s)" % (bits[0], bits[1], allowed),
                )

    def test_set_binary_leaf_with_complex_length(self):
        for bits in [
            (b"1", False),
            (b"12", True),
            (b"123", True),
            (b"12345", False),
            (b"123456", True),
            (b"123456789_", True),
            (b"123456789_123456789_123456789_123456789_12", True),
            (b"123456789_123456789_123456789_123456789_123", False),
        ]:
            with self.subTest(bits=bits):
                allowed = True
                try:
                    self.binary_obj.container.b5 = bits[0]
                except ValueError:
                    allowed = False
                self.assertEqual(
                    allowed,
                    bits[1],
                    "Limited length binary with complex length incorrectly set to %s (%s != %s)"
                    % (bits[0], bits[1], allowed),
                )


if __name__ == "__main__":
    unittest.main()
