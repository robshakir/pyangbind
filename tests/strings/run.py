#!/usr/bin/env python
from __future__ import unicode_literals

import unittest

from tests.base import PyangBindTestCase


class StringTests(PyangBindTestCase):
    yang_files = ["string.yang"]

    def setUp(self):
        self.instance = self.bindings.string()

    def test_string_leaf_is_not_changed_by_default(self):
        self.assertFalse(self.instance.string_container.string_leaf._changed())

    def test_set_basic_string_value_on_string_leaf(self):
        self.instance.string_container.string_leaf = "TestValue"
        self.assertEqual(self.instance.string_container.string_leaf, "TestValue")

    def test_integer_gets_cast_to_string(self):
        self.instance.string_container.string_leaf = 1
        self.assertEqual(self.instance.string_container.string_leaf, "1")

    def test_string_leaf_gets_marked_as_changed(self):
        self.instance.string_container.string_leaf = "TestValue"
        self.assertTrue(self.instance.string_container.string_leaf._changed())

    def test_concatenation_to_string_leaf(self):
        self.instance.string_container.string_leaf = "TestValue"
        self.instance.string_container.string_leaf += "Addition"
        self.assertEqual(self.instance.string_container.string_leaf, "TestValueAddition")

    def test_string_leaf_with_default_is_blank(self):
        self.assertEqual(self.instance.string_container.string_default_leaf, "")

    def test_string_leaf_with_default_has_correct_default_value_hidden(self):
        self.assertEqual(self.instance.string_container.string_default_leaf._default, "string")

    def test_string_leaf_with_default_and_pattern_has_correct_default_value_hidden(self):
        self.assertEqual(self.instance.string_container.restricted_string_default._default, "beep")

    def test_set_valid_value_on_restricted_string(self):
        allowed = True
        try:
            self.instance.string_container.restricted_string = "aardvark"
        except ValueError:
            allowed = False
        self.assertTrue(allowed)

    def test_set_invalid_value_on_restricted_string(self):
        with self.assertRaises(ValueError):
            self.instance.string_container.restricted_string = "bear"

    def test_fixed_length_string(self):
        for (value, valid) in [("a", False), ("ab", True), ("abc", False)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.string_container.restricted_length_string = value
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_fixed_length_string_with_pattern(self):
        for (value, valid) in [("a", False), ("ba", False), ("abc", False), ("ab", True)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.string_container.restricted_length_and_pattern_string = value
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_string_with_length_as_range_with_max(self):
        for (value, valid) in [("short", False), ("loooooooong", True)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.string_container.restricted_length_string_with_range = value
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_string_with_length_as_range_with_upper_bound(self):
        for (value, valid) in [("short", False), ("loooooooong", True), ("toooooooooolooooooooong", False)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.string_container.restricted_length_string_range_two = value
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_string_leaf_with_complex_length(self):
        for (value, valid) in [
            ("strLength10", True),
            ("LengthTwelve", True),
            ("strTwentyOneCharsLong", False),
            ("aReallyLongStringMoreThan30CharsLong", True),
            ("anEvenLongerStringThatIsMoreThanFortyChars", False),
        ]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.string_container.stringLeafWithComplexLength = value
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_string_leaf_pattern_with_dollar(self):
        for (value, valid) in [("fi$h", True), ("void", False), ("fi$ho", True)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.string_container.stringLeafWithPatternWithDollar = value
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_string_leaf_pattern_with_dollar_at_end(self):
        for (value, valid) in [("fi$h", True), ("void", False), ("fi$ho", False)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.string_container.dollarAtEnd = value
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)


if __name__ == "__main__":
    unittest.main()
