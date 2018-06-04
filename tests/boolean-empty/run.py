#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class BooleanEmptyTests(PyangBindTestCase):
    yang_files = ["boolean-empty.yang"]

    def setUp(self):
        self.boolean_obj = self.bindings.boolean_empty()

    def test_leafs_exist(self):
        for leaf in ["b1", "b2", "e1"]:
            with self.subTest(leaf=leaf):
                self.assertTrue(
                    hasattr(self.boolean_obj.container, leaf), "Element did not exist in container (%s)" % leaf
                )

    def test_boolean_leaf_accepts_boolean_values(self):
        for value in [0, "0", False, "false", "False", 1, "1", True, "true", "True"]:
            with self.subTest(value=value):
                allowed = True
                try:
                    self.boolean_obj.container.b1 = value
                except ValueError:
                    allowed = False
                self.assertTrue(allowed, "Value of b1 was not correctly set to %s" % value)

    def test_boolean_leaf_sets_boolean_values_correctly(self):
        for value in [
            (0, False),
            ("0", False),
            (False, False),
            ("false", False),
            ("False", False),
            (1, True),
            ("1", True),
            (True, True),
            ("true", True),
            ("True", True),
        ]:
            with self.subTest(value=value):
                try:
                    self.boolean_obj.container.b1 = value[0]
                except ValueError:
                    pass
                self.assertEqual(
                    self.boolean_obj.container.b1,
                    value[1],
                    "Value of b1 was not correctly set when compared (%s - set to %s)"
                    % (self.boolean_obj.container.b1, value),
                )

    def test_empty_leaf_accepts_boolean_values(self):
        for value in [0, "0", False, "false", "False", 1, "1", True, "true", "True"]:
            with self.subTest(value=value):
                allowed = True
                try:
                    self.boolean_obj.container.e1 = value
                except ValueError:
                    allowed = False
                self.assertTrue(allowed, "Value of e1 was not correctly set to %s" % value)

    def test_empty_leaf_sets_boolean_values_correctly(self):
        for value in [
            (0, False),
            ("0", False),
            (False, False),
            ("false", False),
            ("False", False),
            (1, True),
            ("1", True),
            (True, True),
            ("true", True),
            ("True", True),
        ]:
            with self.subTest(value=value):
                try:
                    self.boolean_obj.container.e1 = value[0]
                except ValueError:
                    pass
                self.assertEqual(
                    self.boolean_obj.container.e1,
                    value[1],
                    "Value of e1 was not correctly set when compared (%s - set to %s)"
                    % (self.boolean_obj.container.e1, value),
                )

    def test_boolean_leaf_default_value(self):
        self.assertFalse(
            self.boolean_obj.container.b2._default,
            "Value default was not correctly set (%s)" % self.boolean_obj.container.b2._default,
        )

    def test_boolean_leaf_is_not_changed_by_default(self):
        self.assertFalse(
            self.boolean_obj.container.b2._changed(),
            "Value was marked as changed incorrectly (%s)" % self.boolean_obj.container.b2._changed(),
        )

    def test_boolean_leaf_sets_changed(self):
        self.boolean_obj.container.b2 = True
        self.assertTrue(
            self.boolean_obj.container.b2._changed(),
            "Value was not flagged as changed (%s != True)" % self.boolean_obj.container.b2._changed(),
        )

    def test_get(self):
        self.boolean_obj.container.b1 = True
        self.boolean_obj.container.e1 = True
        self.assertEqual(
            self.boolean_obj.get(),
            {"container": {"e1": True, "b1": True, "b2": False}},
            "Wrong result returned from get() (%s)" % self.boolean_obj.get(),
        )


if __name__ == "__main__":
    unittest.main()
