#!/usr/bin/env python

from __future__ import unicode_literals

import unittest

import six
from bitarray import bitarray

from tests.base import PyangBindTestCase


class UnionTests(PyangBindTestCase):
    yang_files = ["union.yang"]

    def setUp(self):
        self.instance = self.bindings.union()

    # u1: precedence of int over string
    def test_union_of_int_over_string_allows_math_on_integer_value(self):
        self.instance.container.u1 = 2
        self.instance.container.u1 += 1
        self.assertEqual(self.instance.container.u1, 3)

    def test_set_union_of_int_over_string_to_string_after_int(self):
        self.instance.container.u1 = 3
        self.instance.container.u1 = "aStringTest"
        self.assertEqual(self.instance.container.u1, "aStringTest")

    def test_union_of_int_over_string_allows_concatenation_to_string_value(self):
        self.instance.container.u1 = "aStringTest"
        self.instance.container.u1 += "A"
        self.assertEqual(self.instance.container.u1, "aStringTestA")

    # u2: precedence of string over int, with a default set
    def test_union_of_string_over_int_with_default_is_empty_string(self):
        self.assertEqual(self.instance.container.u2, "")

    def test_default_value_of_string_over_int_with_default(self):
        self.assertEqual(self.instance.container.u2._default, "set from u2")

    def test_union_of_string_over_int_performs_string_concatenation(self):
        self.instance.container.u2 = 2
        self.instance.container.u2 += "A"
        self.assertEqual(self.instance.container.u2, "2A")

    # u3: union of int with precendence over string, but default is a string
    def test_default_value_of_int_over_string_is_zero(self):
        self.assertEqual(self.instance.container.u3, 0)

    def test_default_value_of_int_over_string_with_default_string(self):
        self.assertEqual(self.instance.container.u3._default, "set from u3")

    def test_union_of_int_over_string_with_int_default_is_int_type(self):
        self.assertIsInstance(self.instance.container.u4._default, six.integer_types)

    def test_default_value_gets_set_from_typedef(self):
        self.assertIsInstance(self.instance.container.u6._default, six.text_type)

    def test_set_typedef_union_of_int_over_string_to_a_string_value(self):
        self.instance.container.u7 = "hello"
        self.assertEqual(self.instance.container.u7, "hello")

    def test_set_typedef_union_of_int_over_string_to_int_value_after_string(self):
        self.instance.container.u7 = "hello"
        self.instance.container.u7 = 10
        self.assertEqual(self.instance.container.u7, 10)

    def test_default_value_of_int_typedef_within_union_typedef(self):
        self.assertEqual(self.instance.container.u8._default, 10)

    def test_leaf_list_with_union_of_unions_from_typedefs(self):
        for (value, valid) in [(1, True), ("hello", True), (42.42, True), (True, True), (bitarray(10), False)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.container.u9.append(value)
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_leaf_list_with_union_of_unions_from_typedefs_with_restricted_types(self):
        for (value, valid) in [
            (15, True),
            (35, True),
            ("aardvark", True),
            ("bear", True),
            (21, False),
            (42, False),
            ("cat", False),
            ("fish", False),
        ]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.container.u10.append(value)
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)

    def test_union_of_unions_from_typedefs_with_local_default_gets_proper_default(self):
        self.assertIsInstance(self.instance.container.u11._default, six.text_type)

    def test_union_of_restricted_class_types(self):
        for (value, valid) in [("unlimited", True), (1, True), (0, True), ("fish", False), (2 ** 64, False)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    self.instance.container.u12 = value
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)


if __name__ == "__main__":
    unittest.main()
