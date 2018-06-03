#!/usr/bin/env python

from decimal import Decimal
import unittest

from tests.base import PyangBindTestCase


class DecimalTests(PyangBindTestCase):
    yang_files = ["decimal.yang"]

    def setUp(self):
        self.decimal_obj = self.bindings.decimal_()

    def test_container_has_all_leafs(self):
        for leaf in ["d1", "d2", "d3"]:
            with self.subTest(leaf=leaf):
                self.assertTrue(hasattr(self.decimal_obj.container, leaf), "Container missing attribute - %s" % leaf)

    def test_decimal_precision(self):
        self.decimal_obj.container.d1 = 42.0
        self.assertEqual(
            str(self.decimal_obj.container.d1),
            "42.00",
            "Precision for d1 was incorrect %s" % self.decimal_obj.container.d1,
        )

    def test_decimal_rounding(self):
        self.decimal_obj.container.d2 = 42.0009
        self.assertEqual(
            self.decimal_obj.container.d2,
            Decimal("42.001"),
            "Precision did not result in correct rounding (%s)" % self.decimal_obj.container.d2,
        )

    def test_decimal_default_with_extra_precision(self):
        self.assertEqual(
            self.decimal_obj.container.d2._default,
            Decimal("42.000"),
            "Default was wrong for d2 (%s)" % self.decimal_obj.container.d2._default,
        )

    def test_decimal_default_with_less_precision(self):
        self.assertEqual(
            self.decimal_obj.container.d3._default,
            Decimal("1"),
            "Default was set wrong for d3 (%s)" % self.decimal_obj.container.d3._default,
        )

    def test_various_values_with_complex_range(self):
        for value in [
            (-452.6729, False),
            (-444.44, True),
            (-443.22, False),
            (-330, True),
            (-222.21, False),
            (111.2, False),
            (111.1, True),
            (446.56, True),
            (555.55559282, False),
        ]:
            with self.subTest(value=value):
                allowed = True
                try:
                    self.decimal_obj.container.dec64LeafWithRange = value[0]
                except ValueError:
                    allowed = False
                self.assertEqual(
                    allowed,
                    value[1],
                    "Decimal64 leaf with range was not correctly set (%f -> %s != %s)" % (value[0], allowed, value[1]),
                )


if __name__ == "__main__":
    unittest.main()
