#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class IntTests(PyangBindTestCase):
    yang_files = ["int.yang"]

    def setUp(self):
        self.int_obj = self.bindings.int_()

    def test_all_leafs_are_present(self):
        for name in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
            for subname in ["", "default", "result", "restricted"]:
                with self.subTest(name=name, subname=subname):
                    self.assertTrue(
                        hasattr(self.int_obj.int_container, "%s%s" % (name, subname)),
                        "missing %s%s from container" % (name, subname),
                    )

    def test_default_values(self):
        for pair in [
            ("eightdefault", 2 ** 7 - 1),
            ("sixteendefault", 2 ** 15 - 1),
            ("thirtytwodefault", 2 ** 31 - 1),
            ("sixtyfourdefault", 2 ** 63 - 1),
        ]:
            with self.subTest(pair=pair):
                default_val = getattr(self.int_obj.int_container, pair[0])._default
                self.assertEqual(
                    default_val,
                    pair[1],
                    "default incorrectly set for %s, expected: %d, got %d" % (pair[0], pair[1], default_val),
                )

    def test_set_int_values(self):
        for leaf in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
            with self.subTest(leaf=leaf):
                setattr(self.int_obj.int_container, leaf, 42)
                value = getattr(self.int_obj.int_container, leaf)
                self.assertEqual(value, 42, "incorrectly set %s, expected 42, got %d" % (leaf, value))

    def test_set_int_values_marks_changed(self):
        for leaf in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
            with self.subTest(leaf=leaf):
                setattr(self.int_obj.int_container, leaf, 42)
                leaf_ref = getattr(self.int_obj.int_container, leaf)
                self.assertTrue(leaf_ref._changed(), "incorrect changed flag for %s" % leaf)

    def test_leaf_math_and_negatives(self):
        leafs = ["eight", "sixteen", "thirtytwo", "sixtyfour"]
        for leaf in leafs:
            setattr(self.int_obj.int_container, leaf, 42)

        # Setting these dynamically in a loop just doesn't seem worth the effort of figuring out.
        self.int_obj.int_container.eight *= -1
        self.int_obj.int_container.sixteen *= -1
        self.int_obj.int_container.thirtytwo *= -1
        self.int_obj.int_container.sixtyfour *= -1

        for leaf in leafs:
            with self.subTest(leaf=leaf):
                value = getattr(self.int_obj.int_container, leaf)
                self.assertEqual(value, -42, "Incorrectly set %s, expected 42, got %d" % (leaf, value))

    def test_set_restricted_values_within_allowed_range(self):
        for leaf in ["eightrestricted", "sixteenrestricted", "thirtytworestricted", "sixtyfourrestricted"]:
            with self.subTest(leaf=leaf):
                allowed = True
                try:
                    setattr(self.int_obj.int_container, leaf, 10)
                except ValueError:
                    allowed = False
                self.assertTrue(allowed, "Could not set value of %s to 10" % leaf)

    def test_set_values_outside_allowed_range(self):
        for pair in [
            ("eightrestricted", -100),
            ("eightrestricted", 1001),
            ("sixteenrestricted", -43),
            ("sixteenrestricted", 1001),
            ("thirtytworestricted", 500001),
            ("thirtytworestricted", -43),
            ("sixtyfourrestricted", 72036854775809),
            ("sixtyfourrestricted", -43),
        ]:
            with self.subTest(pair=pair):
                allowed = True
                try:
                    setattr(self.int_obj.int_container, pair[0], pair[1])
                except ValueError:
                    allowed = False
                self.assertFalse(
                    allowed, "Incorrectly allowed value outside of range for %s (%d)" % (pair[0], pair[1])
                )

    def test_int8_max_range(self):
        for pair in [(0, True), (10, True), (-10, False)]:
            with self.subTest(pair=pair):
                allowed = True
                try:
                    self.int_obj.int_container.restricted_ueight_max = pair[0]
                except ValueError:
                    allowed = False
                self.assertEqual(
                    allowed,
                    pair[1],
                    "Restricted range using max was not set correctly (%d -> %s != %s)" % (pair[0], allowed, pair[1]),
                )

    def test_int8_min_range(self):
        for pair in [(0, True), (10, True), (-128, True), (-300, False)]:
            with self.subTest(pair=pair):
                allowed = True
                try:
                    self.int_obj.int_container.restricted_ueight_min = pair[0]
                except ValueError:
                    allowed = False
                self.assertEqual(
                    allowed,
                    pair[1],
                    "Restricted range using min was not set correctly (%s -> %s != %s)" % (pair[0], allowed, pair[1]),
                )

    def test_int8_min_range_alias(self):
        for pair in [(0, True), (10, True), (-128, True), (-300, False)]:
            with self.subTest(pair=pair):
                allowed = True
                try:
                    self.int_obj.int_container.restricted_ueight_min = pair[0]
                except ValueError:
                    allowed = False
                self.assertEqual(
                    allowed,
                    pair[1],
                    "Restricted range using min alias was not set correctly (%s -> %s != %s)"
                    % (pair[0], allowed, pair[1]),
                )

    def test_complex_range_with_two_segments(self):
        for pair in [(0, True), (13, False), (-20, False), (5, True), (16, True)]:
            with self.subTest(pair=pair):
                allowed = True
                try:
                    self.int_obj.int_container.complex_range = pair[0]
                except ValueError:
                    allowed = False
                self.assertEqual(
                    allowed,
                    pair[1],
                    "Complex range was not set correctly (%d -> %s != %s)" % (pair[0], allowed, pair[1]),
                )

    def test_complex_range_with_three_segments_and_spaces(self):
        for pair in [(0, True), (13, False), (-20, False), (5, True), (16, True)]:
            with self.subTest(pair=pair):
                allowed = True
                try:
                    self.int_obj.int_container.complex_range_two = pair[0]
                except ValueError:
                    allowed = False
                self.assertEqual(
                    allowed,
                    pair[1],
                    "Complex range with spaces and three elements was not set correctly (%d -> %s != %s)"
                    % (pair[0], allowed, pair[1]),
                )

    def test_complex_range_with_negative(self):
        for pair in [(-2, True), (42, False)]:
            with self.subTest(pair=pair):
                allowed = True
                try:
                    self.int_obj.int_container.complex_range_with_negative = pair[0]
                except ValueError:
                    allowed = False
                self.assertEqual(
                    allowed,
                    pair[1],
                    "Complex range with negatives was not set correctly (%d -> %s != %s)"
                    % (pair[0], allowed, pair[1]),
                )

    def test_int8_range_with_negatives_and_spaces(self):
        for pair in [(-11, False), (-5, True), (0, False), (5, False), (10, True), (25, True), (31, False)]:
            with self.subTest(pair=pair):
                allowed = True
                try:
                    self.int_obj.int_container.intLeafWithRange = pair[0]
                except ValueError:
                    allowed = False
                self.assertEqual(
                    allowed,
                    pair[1],
                    "Complex range with negatives and additional spaces was not set correctly (%d -> %s != %s)"
                    % (pair[0], allowed, pair[1]),
                )

    def test_complex_range_with_equals_case(self):
        for pair in [(-43, False), (-40, True), (98, False), (122, True), (254, False), (255, True), (256, False)]:
            with self.subTest(pair=pair):
                allowed = True
                try:
                    self.int_obj.int_container.complex_range_with_equals_case = pair[0]
                except ValueError:
                    allowed = False
                self.assertEqual(
                    allowed,
                    pair[1],
                    "Complex range with equals case was not set correctly (%d -> %s != %s)"
                    % (pair[0], allowed, pair[1]),
                )

    def test_setters_exist(self):
        for leaf in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
            with self.subTest(leaf=leaf):
                setter = getattr(self.int_obj.int_container, "_set_%s" % leaf, None)
                self.assertIsNotNone(setter, "Could not find attribute setter for %s" % leaf)

    def test_set_int_sizes_at_lower_bounds(self):
        bounds = {"eight": -2 ** 7, "sixteen": -2 ** 15, "thirtytwo": -2 ** 31, "sixtyfour": -2 ** 63}
        for leaf, value in bounds.items():
            with self.subTest(leaf=leaf):
                setter = getattr(self.int_obj.int_container, "_set_%s" % leaf)
                allowed = True
                try:
                    setter(value)
                except ValueError:
                    allowed = False
                self.assertTrue(allowed, "Could not set int size %s to %d" % (leaf, value))

    def test_set_int_sizes_below_lower_bounds(self):
        bounds = {"eight": -2 ** 7 - 1, "sixteen": -2 ** 15 - 1, "thirtytwo": -2 ** 31 - 1, "sixtyfour": -2 ** 63 - 1}
        for leaf, value in bounds.items():
            with self.subTest(leaf=leaf):
                setter = getattr(self.int_obj.int_container, "_set_%s" % leaf)
                allowed = True
                try:
                    setter(value)
                except ValueError:
                    allowed = False
                self.assertFalse(allowed, "Incorrectly set int size %s to %d" % (leaf, value))

    def test_set_int_sizes_at_upper_bounds(self):
        bounds = {"eight": 2 ** 7 - 1, "sixteen": 2 ** 15 - 1, "thirtytwo": 2 ** 31 - 1, "sixtyfour": 2 ** 63 - 1}
        for leaf, value in bounds.items():
            with self.subTest(leaf=leaf):
                setter = getattr(self.int_obj.int_container, "_set_%s" % leaf)
                allowed = True
                try:
                    setter(value)
                except ValueError:
                    allowed = False
                self.assertTrue(allowed, "Could not set int size %s to %d" % (leaf, value))

    def test_set_int_sizes_above_upper_bounds(self):
        bounds = {"eight": 2 ** 7, "sixteen": 2 ** 15, "thirtytwo": 2 ** 31, "sixtyfour": 2 ** 63}
        for leaf, value in bounds.items():
            with self.subTest(leaf=leaf):
                setter = getattr(self.int_obj.int_container, "_set_%s" % leaf)
                allowed = True
                try:
                    setter(value)
                except ValueError:
                    allowed = False
                self.assertFalse(allowed, "Incorrectly set int size %s to %d" % (leaf, value))

    def test_set_int8_range_with_min_max_alias_to_lower_bound(self):
        allowed = True
        try:
            self.int_obj.int_container.restricted_ueight_min_alias = -2 ** 7
        except ValueError:
            allowed = False
        self.assertTrue(allowed, "Could not set min..max int8 to minimum value")

    def test_set_int8_range_with_min_max_alias_to_upper_bound(self):
        allowed = True
        try:
            self.int_obj.int_container.restricted_ueight_min_alias = 2 ** 7 - 1
        except ValueError:
            allowed = False
        self.assertTrue(allowed, "Could not set min..max int8 to maximum value")

    def test_set_int8_range_with_min_max_alias_below_lower_bound(self):
        allowed = True
        try:
            self.int_obj.int_container.restricted_ueight_min_alias = -2 ** 7 - 1
        except ValueError:
            allowed = False
        self.assertFalse(allowed, "Incorrectly set min..max int8 to the min value minus one")

    def test_set_int8_range_with_min_max_alias_above_upper_bound(self):
        allowed = True
        try:
            self.int_obj.int_container.restricted_ueight_min_alias = 2 ** 7 + 1
        except ValueError:
            allowed = False
        self.assertFalse(allowed, "Incorrectly set min..max int8 to the max value plus one")


if __name__ == "__main__":
    unittest.main()
