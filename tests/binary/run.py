#!/usr/bin/env python

from bitarray import bitarray
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

    def test_set_bitarray_from_different_datatypes(self):
        for value in [("01110", True), ({"42": 42}, True), (-42, False), ("Arthur Dent", False)]:
            with self.subTest(value=value):
                allowed = True
                try:
                    self.binary_obj.container.b1 = value[0]
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, value[1], "Could incorrectly set b1 to %s" % value[0])

    def test_binary_leaf_default_value(self):
        default = bitarray("0100")
        self.assertEqual(
            self.binary_obj.container.b2._default,
            default,
            "Default for leaf b2 was not set correctly (%s != %s)" % (self.binary_obj.container.b2._default, default),
        )

    def test_binary_leaf_is_empty_bitarray_by_default(self):
        empty = bitarray()
        self.assertEqual(
            self.binary_obj.container.b2,
            empty,
            "Value of bitarray was not null when checking b2 (%s != %s)" % (self.binary_obj.container.b2, empty),
        )

    def test_binary_leaf_is_not_changed_by_default(self):
        self.assertFalse(
            self.binary_obj.container.b2._changed(),
            "Unset bitarray specified changed when was default (%s != False)"
            % self.binary_obj.container.b2._changed(),
        )

    def test_set_bitarray_stores_value(self):
        bits = bitarray("010")
        self.binary_obj.container.b2 = bits
        self.assertEqual(
            self.binary_obj.container.b2,
            bits,
            "Bitarray not successfully set (%s != %s)" % (self.binary_obj.container.b2, bits),
        )

    def test_setting_bitarray_set_changed(self):
        self.binary_obj.container.b2 = bitarray("010")
        self.assertTrue(
            self.binary_obj.container.b2._changed(),
            "Bitarray value not flagged as changed (%s != True)" % self.binary_obj.container.b2._changed(),
        )

    def test_set_specific_length_bitarray(self):
        for bits in [("0", False), ("1000000011110000", True), ("111111110000000011111111", False)]:
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

    def test_set_bitarray_with_length_range(self):
        for bits in [
            ("0", False),
            ("1111111100000000", True),
            ("111111110000000011111111", True),
            ("1111111100000000111111110000000011110000", False),
        ]:
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

    def test_set_bitarray_with_complex_length(self):
        for bits in [
            ("0", False),
            ("1111000011110000", True),
            ("111100001111000011110000", True),
            ("1111000011110000111100001111000011110000", False),
            ("111100001111000011110000111100001111000011110000", True),
            ("111100001111000011110000111100001111000011110000" "11110000111100001111000011110000", True),
            (
                "111100001111000011110000111100001111000011110000"
                "111100001111000011110000111100001111000011110000"
                "111100001111000011110000111100001111000011110000"
                "111100001111000011110000111100001111000011110000"
                "111100001111000011110000111100001111000011110000"
                "111100001111000011110000111100001111000011110000"
                "111100001111000011110000111100001111000011110000"
                "1010101010101010",
                False,
            ),
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
