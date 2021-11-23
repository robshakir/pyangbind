#!/usr/bin/env python
from __future__ import unicode_literals

import unittest

from tests.base import PyangBindTestCase


class BitsTests(PyangBindTestCase):
    yang_files = ["bits.yang"]

    def setUp(self):
        self.instance = self.bindings.bits()

    def test_default_bits(self):
        self.assertEqual(
            self.instance.mybits._default,
            set(["flag1", "flag3"]),
        )
        self.assertFalse(self.instance.mybits._changed())

    def test_default_bits_with_in(self):
        self.assertTrue(
            "flag1" in self.instance.mybits._default
            and "flag2" not in self.instance.mybits._default
            and "flag3" in self.instance.mybits._default
        )

    def test_default_bits_is_unchanged(self):
        self.assertFalse(self.instance.mybits._changed())

    def test_set_flags(self):
        for value, valid in [("flag1", True), ("flag2", True), ("unknownflag", False)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.mybits.add(value)
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_check_flags_unset(self):
        self.instance.mybits.discard("flag2")
        self.assertTrue("flag2" not in self.instance.mybits)
        self.assertTrue(self.instance.mybits._changed())

    def test_check_flags_set(self):
        self.instance.bits2.add("foo")
        self.assertTrue("foo" in self.instance.bits2)
        self.assertEqual(set(["foo"]), self.instance.bits2)
        self.assertTrue(self.instance.bits2._changed())

    def test_bits_position(self):
        self.instance.bits2.add("bar")
        self.instance.bits2.add("baz")
        self.instance.bits2.add("foo")
        self.assertEqual(str(self.instance.bits2), "foo bar baz")


if __name__ == "__main__":
    unittest.main()
