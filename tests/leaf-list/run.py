#!/usr/bin/env python
from __future__ import unicode_literals

from tests.base import PyangBindTestCase

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class LeafListTests(PyangBindTestCase):
    yang_files = ["leaflist.yang"]

    def setUp(self):
        self.leaflist_obj = self.bindings.leaflist()

    def test_container_exists(self):
        self.assertTrue(hasattr(self.leaflist_obj, "container"))

    def test_leaflist_exists(self):
        self.assertTrue(hasattr(self.leaflist_obj.container, "leaflist"))

    def test_leaflist_length_is_zero(self):
        self.assertEqual(len(self.leaflist_obj.container.leaflist), 0)

    def test_append_to_leaflist(self):
        self.leaflist_obj.container.leaflist.append("itemOne")
        self.assertEqual(len(self.leaflist_obj.container.leaflist), 1)

    def test_retrieve_leaflist_item_value(self):
        self.leaflist_obj.container.leaflist.append("itemOne")
        self.assertEqual(self.leaflist_obj.container.leaflist[0], "itemOne")

    def test_append_int_to_string_leaflist(self):
        with self.assertRaises(ValueError):
            self.leaflist_obj.container.leaflist.append(1)

    def test_getitem(self):
        self.leaflist_obj.container.leaflist.append("itemOne")
        self.leaflist_obj.container.leaflist.append("itemTwo")

        self.assertEqual(self.leaflist_obj.container.leaflist[1], "itemTwo")

    def test_setitem(self):
        self.leaflist_obj.container.leaflist.append("itemOne")
        self.leaflist_obj.container.leaflist.append("itemTwo")
        self.leaflist_obj.container.leaflist[1] = "indexOne"

        self.assertEqual(self.leaflist_obj.container.leaflist[1], "indexOne")

    def test_insert(self):
        self.leaflist_obj.container.leaflist.append("itemOne")
        self.leaflist_obj.container.leaflist.append("itemTwo")
        self.leaflist_obj.container.leaflist[1] = "indexOne"
        self.leaflist_obj.container.leaflist.insert(0, "indexZero")

        self.assertEqual(self.leaflist_obj.container.leaflist[0], "indexZero")

    def test_leaflist_grows_from_various_modification_methods(self):
        self.leaflist_obj.container.leaflist.append("itemOne")
        self.leaflist_obj.container.leaflist.append("itemTwo")
        self.leaflist_obj.container.leaflist[1] = "indexOne"
        self.leaflist_obj.container.leaflist.insert(0, "indexZero")

        self.assertEqual(len(self.leaflist_obj.container.leaflist), 4)

    def test_delete_item_from_leaflist(self):
        self.leaflist_obj.container.leaflist.append("itemOne")
        self.leaflist_obj.container.leaflist.append("itemTwo")
        self.leaflist_obj.container.leaflist[1] = "indexOne"
        self.leaflist_obj.container.leaflist.insert(0, "indexZero")

        del self.leaflist_obj.container.leaflist[0]

        self.assertEqual(len(self.leaflist_obj.container.leaflist), 3)

    def test_get_full_leaflist(self):
        self.leaflist_obj.container.leaflist.append("itemOne")
        self.leaflist_obj.container.leaflist.append("itemTwo")
        self.leaflist_obj.container.leaflist[1] = "indexOne"
        self.leaflist_obj.container.leaflist.insert(0, "indexZero")
        del self.leaflist_obj.container.leaflist[0]

        self.assertEqual(
            self.leaflist_obj.get(),
            {"container": {"leaflist": ["itemOne", "indexOne", "itemTwo"], "listtwo": [], "listthree": []}},
        )

    def test_leaflist_assignment(self):
        self.leaflist_obj.container.leaflist = ["itemOne", "itemTwo"]

        self.assertEqual(self.leaflist_obj.container.leaflist, ["itemOne", "itemTwo"])

    def test_leaflist_assignment_of_wrong_type(self):
        with self.assertRaises(ValueError):
            self.leaflist_obj.container.leaflist = [1, 2]

    def test_restricted_string(self):
        self.leaflist_obj.container.listtwo.append("a-valid-string")
        self.assertEqual(len(self.leaflist_obj.container.listtwo), 1)

    def test_restricted_string_invalid_value(self):
        with self.assertRaises(ValueError):
            self.leaflist_obj.container.listtwo.append("broken-string")

    def test_union_type(self):
        for pair in [(1, True), ("fish", True), ([], False)]:
            with self.subTest(pair=pair):
                allowed = True
                try:
                    self.leaflist_obj.container.listthree.append(pair[0])
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, pair[1])

    def test_leaf_lists_are_unique_after_assignment(self):
        self.leaflist_obj.container.leaflist = ["foo", "bar", "foo"]
        self.assertEqual(self.leaflist_obj.container.get(filter=True), {"leaflist": ["foo", "bar"]})

    def test_leaf_lists_are_unique_after_append(self):
        self.leaflist_obj.container.leaflist.append("foo")
        self.leaflist_obj.container.leaflist.append("bar")
        self.leaflist_obj.container.leaflist.append("foo")
        self.assertEqual(self.leaflist_obj.container.get(filter=True), {"leaflist": ["foo", "bar"]})

    def test_leaf_lists_insert_non_unique_value_raises_keyerror(self):
        self.leaflist_obj.container.leaflist[0] = "foo"
        self.leaflist_obj.container.leaflist[1] = "bar"
        with self.assertRaises(ValueError):
            self.leaflist_obj.container.leaflist[2] = "foo"


if __name__ == "__main__":
    unittest.main()
