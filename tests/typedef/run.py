#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class TypedefTests(PyangBindTestCase):
    yang_files = ["typedef.yang"]

    def setUp(self):
        self.typedef = self.bindings.typedef()

    def test_types(self):

        for element in [
            "string",
            "integer",
            "stringdefault",
            "integerdefault",
            "new_string",
            "remote_new_type",
            "session_dir",
            "remote_local_type",
        ]:
            with self.subTest(element=element):
                self.assertTrue(
                    hasattr(self.typedef.container, element), "element %s did not exist within the container" % element
                )

    def test_string_container(self):
        self.typedef.container.string = "hello"
        self.assertEqual(
            self.typedef.container.string,
            "hello",
            "incorrect value set for the strong container (value: %s)" % self.typedef.container.string,
        )

    def test_string_default(self):
        self.assertEqual(
            self.typedef.container.stringdefault._default,
            "aDefaultValue",
            "incorrect default value for derived string type with a default (value: %s)"
            % self.typedef.container.stringdefault._default,
        )

    def test_string_default_from_typedef(self):
        self.assertEqual(
            self.typedef.container.new_string._default,
            "defaultValue",
            "incorrect default value where derived from typedef (value: %s)"
            % self.typedef.container.new_string._default,
        )

    def test_int_value_can_be_updated(self):
        self.typedef.container.integer = 1
        self.assertEqual(self.typedef.container.integer, 1, "integer value not correctly updated")

    def test_int_value_range_restriction(self):
        with self.assertRaises(ValueError, msg="restricted int from typedef was set to invalue value"):
            self.typedef.container.integer = 65

    def test_remote_definition(self):
        self.typedef.container.remote_new_type = "testString"
        self.assertEqual(
            self.typedef.container.remote_new_type,
            "testString",
            "incorrect value for the remote definition (%s)" % self.typedef.container.remote_new_type,
        )

    def test_remote_local_definition(self):
        self.typedef.container.remote_local_type = "testString"
        self.assertEqual(
            self.typedef.container.remote_local_type,
            "testString",
            "incorrect value for remote definition which had local definition (%s)"
            % self.typedef.container.remote_local_type,
        )

    def test_inherited_patterns(self):
        for pattern in [("aardvark", True), ("ant", False), ("duck", False)]:
            with self.subTest(pattern=pattern):
                wset = True
                try:
                    self.typedef.container.inheritance = pattern[0]
                except ValueError:
                    wset = False
                self.assertEqual(
                    wset,
                    pattern[1],
                    "inherited pattern was not correctly followed for %s (%s != %s)" % (pattern[0], pattern[1], wset),
                )

    def test_inherited_range(self):
        for item in [(2, True), (10, False), (1, False)]:
            with self.subTest(item=item):
                wset = True
                try:
                    self.typedef.container.int_inheritance = item[0]
                except ValueError:
                    wset = False
                self.assertEqual(
                    wset,
                    item[1],
                    "inherited range was not correctly followed for %s (%s != %s)" % (item[0], item[1], wset),
                )

    def test_stacked_union(self):
        for item in [("aardvark", True), ("bear", True), ("chicken", False), ("deer", False), ("zebra", True)]:
            with self.subTest(item=item):
                wset = True
                try:
                    self.typedef.container.stacked_union.append(item[0])
                except ValueError:
                    wset = False
                self.assertEqual(
                    wset,
                    item[1],
                    "incorrectly dealt with %s when added as a list key (%s != %s)" % (item[0], wset, item[1]),
                )

    def test_hybrid_typedef_across_modules(self):
        for item in [("zebra", True), ("yak", False)]:
            with self.subTest(item=item):
                wset = True
                try:
                    self.typedef.container.include_of_include_definition = item[0]
                except ValueError:
                    wset = False
                self.assertEqual(
                    wset,
                    item[1],
                    "definition with hybrid typedef across two modules was not set correctly for %s (%s != %s)"
                    % (item[0], item[1], wset),
                )

    def test_identity_reference(self):
        for item in [("IDONE", True), ("IDTWO", True), ("IDTHREE", False)]:
            with self.subTest(item=item):
                wset = True
                try:
                    self.typedef.container.identity_one_typedef = item[0]
                except ValueError:
                    wset = False
                self.assertEqual(
                    wset,
                    item[1],
                    "definition with a typedef which references an identity was not set correctly for %s (%s != %s)"
                    % (item[0], item[1], wset),
                )

    def test_union_with_union(self):
        for item in [("aardvark", True), ("bear", True), ("chicken", False), ("quail", True), ("zebra", False)]:
            with self.subTest(item=item):
                wset = True
                try:
                    self.typedef.container.union_with_union = item[0]
                except ValueError:
                    wset = False
                self.assertEqual(
                    wset,
                    item[1],
                    "definition which was a union including a typedef was not set correctly for %s (%s != %s)"
                    % (item[0], item[1], wset),
                )

    def test_scoped_leaf(self):
        self.typedef.container.scoped_leaf = "aardwolf"
        self.assertEqual(
            self.typedef.container.scoped_leaf,
            "aardwolf",
            "scoped leaf was not set correctly (%s)" % self.typedef.container.scoped_leaf,
        )

    def test_union_with_identityref(self):
        for item in [("IDONE", True), (42, True), (-127, False), ("badstr", False)]:
            with self.subTest(item=item):
                wset = True
                try:
                    self.typedef.container.union_idref = item[0]
                except ValueError:
                    wset = False
                self.assertEqual(
                    wset,
                    item[1],
                    "union with an identityref within it was not set correctly: %s != %s (%s)"
                    % (wset, item[1], item[0]),
                )

    def test_nested_typedefs(self):
        self.typedef.scoped_container_typedef.two = "amber"
        self.assertEqual(
            self.typedef.scoped_container_typedef.two,
            "amber",
            "scoped typedef leaf within a container not set correctly",
        )


if __name__ == "__main__":
    unittest.main()
