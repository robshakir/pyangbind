#!/usr/bin/env python

from __future__ import unicode_literals

import unittest

from tests.base import PyangBindTestCase


class UIntTests(PyangBindTestCase):
    yang_files = ["uint.yang"]

    def setUp(self):
        self.instance = self.bindings.uint()

    def test_uint_maximum_default_values(self):
        for (size, value) in [
            ("eight", 2 ** 8 - 1),
            ("sixteen", 2 ** 16 - 1),
            ("thirtytwo", 2 ** 32 - 1),
            ("sixtyfour", 2 ** 64 - 1),
        ]:
            with self.subTest(size=size, value=value):
                default = getattr(self.instance.uint_container, "%sdefault" % size)._default
                self.assertEqual(default, value)

    def test_set_uint_values(self):
        for leaf in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
            with self.subTest(leaf=leaf):
                setattr(self.instance.uint_container, leaf, 42)
                value = getattr(self.instance.uint_container, leaf)
                self.assertEqual(value, 42)

    def test_set_uint_values_marks_changes(self):
        for leaf in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
            with self.subTest(leaf=leaf):
                setattr(self.instance.uint_container, leaf, 42)
                leaf_ref = getattr(self.instance.uint_container, leaf)
                self.assertTrue(leaf_ref._changed())

    def test_uint8_with_restricted_range(self):
        for (value, valid) in [(0, False), (7, True), (11, False)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.uint_container.eightrestricted = value
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_uint16_with_restricted_range(self):
        for (value, valid) in [(99, False), (123, True), (1001, False)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.uint_container.sixteenrestricted = value
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_uint32_with_restricted_range(self):
        for (value, valid) in [(9999, False), (424242, True), (500001, False)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.uint_container.thirtytworestricted = value
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_uint64_with_restricted_range(self):
        for (value, valid) in [(799, False), (42424242, True), (18446744073709551615, False)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.uint_container.sixtyfourrestricted = value
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_additional_uint32_range(self):
        for (value, valid) in [(0, True), (10, True), (2 ** 32 - 1, True), (2 ** 64, False)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.issue_fixes.region_id = value
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_set_uint_values_to_zero(self):
        for size in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
            with self.subTest(size=size):
                setter = getattr(self.instance.uint_container, "_set_%s" % size)
                allowed = True
                try:
                    setter(0)
                except ValueError:
                    allowed = False
                self.assertTrue(allowed)

    def test_set_uint_values_below_zero(self):
        for size in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
            with self.subTest(size=size):
                setter = getattr(self.instance.uint_container, "_set_%s" % size)
                with self.assertRaises(ValueError):
                    setter(-1)

    def test_set_uint_values_above_upper_bounds(self):
        bounds = {"eight": 2 ** 8, "sixteen": 2 ** 16, "thirtytwo": 2 ** 32, "sixtyfour": 2 ** 64}
        for size, value in bounds.items():
            with self.subTest(size=size, value=value), self.assertRaises(ValueError):
                setter = getattr(self.instance.uint_container, "_set_%s" % size)
                setter(value)


if __name__ == "__main__":
    unittest.main()
