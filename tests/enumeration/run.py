#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class EnumerationTests(PyangBindTestCase):
    yang_files = ["enumeration.yang"]

    def setUp(self):
        self.enum_obj = self.bindings.enumeration()

    def test_container_has_all_leafs(self):
        for leaf in ["e", "f"]:
            with self.subTest(leaf=leaf):
                self.assertTrue(
                    hasattr(self.enum_obj.container, leaf), "Container does not contain enumeration %s" % leaf
                )

    def test_assign_to_enum(self):
        self.enum_obj.container.e = "one"
        self.assertEqual(
            self.enum_obj.container.e,
            "one",
            "Enumeration value was not correctly set (%s)" % self.enum_obj.container.e,
        )

    def test_enum_does_not_allow_invalid_value(self):
        allowed = True
        try:
            self.enum_obj.container.e = "twentyseven"
        except ValueError:
            allowed = False
        self.assertFalse(
            allowed, "Erroneous value was not caught by restriction handler (%s)" % self.enum_obj.container.e
        )

    def test_enum_default_value(self):
        self.assertEqual(
            self.enum_obj.container.f._default,
            "c",
            "Erroneous default value for 'f' (%s)" % self.enum_obj.container.f._default,
        )

    def test_static_enum_value(self):
        self.enum_obj.container.e = "two"
        self.assertEqual(
            self.enum_obj.container.e.getValue(mapped=True),
            42,
            "Erroneously statically defined value returned (%s)" % self.enum_obj.container.e.getValue(mapped=True),
        )


if __name__ == "__main__":
    unittest.main()
