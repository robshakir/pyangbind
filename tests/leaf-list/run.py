#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class LeafListTests(PyangBindTestCase):
  yang_files = ['leaflist.yang']

  def setUp(self):
    self.leaflist_obj = self.bindings.leaflist()

  def test_container_exists(self):
    self.assertTrue(hasattr(self.leaflist_obj, "container"), "Base container is missing.")

  def test_leaflist_exists(self):
    self.assertTrue(hasattr(self.leaflist_obj.container, "leaflist"), "Leaf-list instance is missing.")

  def test_leaflist_length_is_zero(self):
    self.assertEqual(len(self.leaflist_obj.container.leaflist), 0, "Length of leaflist was not zero.")

  def test_append_to_leaflist(self):
    self.leaflist_obj.container.leaflist.append("itemOne")
    self.assertEqual(len(self.leaflist_obj.container.leaflist), 1, "Did not successfully append string to list.")

  def test_retrieve_leaflist_item_value(self):
    self.leaflist_obj.container.leaflist.append("itemOne")
    self.assertEqual(self.leaflist_obj.container.leaflist[0], "itemOne",
      "Cannot successfully address an item from the list.")

  def test_append_int_to_string_leaflist(self):
    allowed = True
    try:
      self.leaflist_obj.container.leaflist.append(1)
    except ValueError:
      allowed = False
    self.assertFalse(allowed, "Appended an element to the list erroneously")

  def test_getitem(self):
    self.leaflist_obj.container.leaflist.append("itemOne")
    self.leaflist_obj.container.leaflist.append("itemTwo")

    self.assertEqual(self.leaflist_obj.container.leaflist[1], "itemTwo", "getitem did not return the correct value.")

  def test_setitem(self):
    self.leaflist_obj.container.leaflist.append("itemOne")
    self.leaflist_obj.container.leaflist.append("itemTwo")
    self.leaflist_obj.container.leaflist[1] = "indexOne"

    self.assertEqual(self.leaflist_obj.container.leaflist[1], "indexOne", "setitem did not set the correct node.")

  def test_insert(self):
    self.leaflist_obj.container.leaflist.append("itemOne")
    self.leaflist_obj.container.leaflist.append("itemTwo")
    self.leaflist_obj.container.leaflist[1] = "indexOne"
    self.leaflist_obj.container.leaflist.insert(0, "indexZero")

    self.assertEqual(self.leaflist_obj.container.leaflist[0], "indexZero", "Incorrectly set index 0 value")

  def test_leaflist_grows_from_various_modification_methods(self):
    self.leaflist_obj.container.leaflist.append("itemOne")
    self.leaflist_obj.container.leaflist.append("itemTwo")
    self.leaflist_obj.container.leaflist[1] = "indexOne"
    self.leaflist_obj.container.leaflist.insert(0, "indexZero")

    self.assertEqual(len(self.leaflist_obj.container.leaflist), 4, "List item was not added by insert()")

  def test_delete_item_from_leaflist(self):
    self.leaflist_obj.container.leaflist.append("itemOne")
    self.leaflist_obj.container.leaflist.append("itemTwo")
    self.leaflist_obj.container.leaflist[1] = "indexOne"
    self.leaflist_obj.container.leaflist.insert(0, "indexZero")

    del self.leaflist_obj.container.leaflist[0]

    self.assertEqual(len(self.leaflist_obj.container.leaflist), 3, "List item not successfully removed by delitem")

  def test_get_full_leaflist(self):
    self.leaflist_obj.container.leaflist.append("itemOne")
    self.leaflist_obj.container.leaflist.append("itemTwo")
    self.leaflist_obj.container.leaflist[1] = "indexOne"
    self.leaflist_obj.container.leaflist.insert(0, "indexZero")
    del self.leaflist_obj.container.leaflist[0]

    self.assertEqual(
      self.leaflist_obj.get(),
      {'container': {'leaflist': ['itemOne', 'indexOne', 'itemTwo'],
                     'listtwo': [],
                     'listthree': []}},
      "get did not correctly return the dictionary"
    )

  def test_leaflist_assignment(self):
    self.leaflist_obj.container.leaflist = ["itemOne", "itemTwo"]

    self.assertEqual(self.leaflist_obj.container.leaflist, ["itemOne", "itemTwo"],
      "Leaflist assignment did not function correctly")

  def test_leaflist_assignment_of_wrong_type(self):
    allowed = True
    try:
      self.leaflist_obj.container.leaflist = [1, 2]
    except ValueError:
      allowed = False
    self.assertFalse(allowed, "An erroneous value was assigned to the list.")

  def test_restricted_string(self):
    self.leaflist_obj.container.listtwo.append("a-valid-string")
    self.assertEqual(len(self.leaflist_obj.container.listtwo), 1, "Restricted lefalist did not function correctly.")

  def test_restricted_string_invalid_value(self):
    allowed = True
    try:
      self.leaflist_obj.container.listtwo.append("broken-string")
    except ValueError:
      allowed = False
    self.assertFalse(allowed, "An erroneous value was assigned to the list (restricted type)")

  def test_union_type(self):
    for pair in [(1, True), ("fish", True), ([], False)]:
      with self.subTest(pair=pair):
        allowed = True
        try:
          self.leaflist_obj.container.listthree.append(pair[0])
        except ValueError:
          allowed = False
        self.assertEqual(allowed, pair[1], "leaf-list of union type had invalid result (%s != %s for %s)" %
          (allowed, pair[1], pair[0]))


if __name__ == '__main__':
  unittest.main()
