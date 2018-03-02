#!/usr/bin/env python
import unittest

from pyangbind.lib.xpathhelper import YANGPathHelper
from tests.base import PyangBindTestCase


class XPathListLeaflistTests(PyangBindTestCase):
  yang_files = ['list-tc01.yang']

  def setUp(self):
    self.path_helper = YANGPathHelper()
    self.yang_obj = self.bindings.list_tc01(path_helper=self.path_helper)

  def test_set_leaflist(self):
    for a in ["mackerel", "trout", "haddock", "flounder"]:
      self.yang_obj.container.t1.append(a)
    for item in [("mackerel", True), ("haddock", True), ("minnow", False)]:
      with self.subTest(item=item):
        valid = True
        try:
          self.yang_obj.reference.t1_ptr = item[0]
        except ValueError:
          valid = False
        self.assertEqual(valid, item[1], "Reference was incorrectly set for a leaflist (%s not in %s -> %s != %s)" %
          (item[0], str(self.yang_obj.container.t1), valid, item[1]))

  def test_set_leaflist_with_no_require_instance(self):
    for a in ["mackerel", "trout", "haddock", "flounder"]:
      self.yang_obj.container.t1.append(a)
    for item in [("flounder", "exists"), ("minnow", "does not exist")]:
      with self.subTest(item=item):
        valid = True
        try:
          self.yang_obj.reference.t1_ptr_noexist = item[0]
        except ValueError:
          valid = False
        self.assertTrue(valid,
          "Reference was incorrectly set for a leaflist with require_instance set to false "
          "(%s threw error, but it %s)" % (item[0], item[1]))

  def test_set_list(self):
    for o in ["kangaroo", "wallaby", "koala", "dingo"]:
      self.yang_obj.container.t2.add(o)

    for item in [("kangaroo", True), ("koala", True), ("wombat", False)]:
      with self.subTest(item=item):
        valid = True
        try:
          self.yang_obj.reference.t2_ptr = item[0]
        except ValueError:
          valid = False
        self.assertEqual(valid, item[1], "Reference was incorrectly set for a list (%s not in %s -> %s != %s)" %
          (item[0], self.yang_obj.container.t2.keys(), valid, item[1]))

  def test_leaflist_returns_single_element(self):
    for b in ["oatmeal-stout", "amber-ale", "pale-ale", "pils",
              "ipa", "session-ipa"]:
      self.yang_obj.container.t3.append(b)

    leaflist = self.path_helper.get("/container/t3")
    self.assertEqual(len(leaflist), 1,
      "Looking up a leaf-list element returned multiple elements erroneously (%d elements (%s))" %
      (len(leaflist), leaflist))

  def test_leaflist_can_find_known_values(self):
    for b in ["oatmeal-stout", "amber-ale", "pale-ale", "pils",
              "ipa", "session-ipa"]:
      self.yang_obj.container.t3.append(b)

    leaflist = self.path_helper.get("/container/t3")
    for item in [("session-ipa", True), ("amber-ale", True), ("moose-drool", False)]:
      with self.subTest(item=item):
        found = True
        try:
          leaflist[0].index(item[0])
        except ValueError:
          found = False

        self.assertEqual(found, item[1],
          "When retrieving a leaf-list element, a known value was not in the list (%s -> %s (%s))" %
          (item[0], item[1], leaflist[0]))

  def test_can_remove_items_from_leaflist(self):
    for b in ["oatmeal-stout", "amber-ale", "pale-ale", "pils",
              "ipa", "session-ipa"]:
      self.yang_obj.container.t3.append(b)

    for item in [("session-ipa", True), ("amber-ale", True), ("moose-drool", False)]:
      with self.subTest(item=item):
        removed = True
        try:
          self.yang_obj.container.t3.remove(item[0])
        except ValueError:
          removed = False
        self.assertEqual(removed, item[1],
          "Removal of a leaflist element did not return expected result (%s -> %s != %s)" %
          (item[0], removed, item[1]))

  def test_removed_leaflist_item_is_gone_from_tree(self):
    for b in ["oatmeal-stout", "amber-ale", "pale-ale", "pils",
              "ipa", "session-ipa"]:
      self.yang_obj.container.t3.append(b)

    for item in [("session-ipa", True), ("amber-ale", True), ("moose-drool", False)]:
      with self.subTest(item=item):
        try:
          self.yang_obj.container.t3.remove(item[0])
        except ValueError:
          pass
        leaflist = self.path_helper.get("/container/t3")
        found = True
        try:
          leaflist[0].index(item[0])
        except ValueError:
          found = False
        self.assertFalse(found, "An element was not correctly removed from the leaf-list (%s -> %s [%s])" %
          (item[0], "/container/t3", leaflist[0]))

  def test_list_returns_single_element(self):
    for b in ["steam", "liberty", "california-lager", "porter", "ipa",
              "foghorn"]:
      self.yang_obj.container.t4.add(b)

    for item in [("steam", 1), ("liberty", 1), ("pygmy-owl", 0)]:
      with self.subTest(item=item):
        path = "/container/t4[keyval=%s]" % item[0]
        leaf = self.path_helper.get(path)
        self.assertEqual(len(leaf), item[1],
          "Retrieval of a list element returned the wrong number of elements (%s -> %d != %d)" %
          (item[0], len(leaf), item[1]))

  def test_remove_list_item(self):
    for b in ["steam", "liberty", "california-lager", "porter", "ipa",
              "foghorn"]:
      self.yang_obj.container.t4.add(b)

    for item in [("steam", True), ("liberty", True), ("pygmy-owl", False)]:
      with self.subTest(item=item):
        removed = True
        try:
          self.yang_obj.container.t4.delete(item[0])
        except KeyError:
          removed = False
        self.assertEqual(removed, item[1],
          "Removal of a list element did not return expected result (%s -> %s != %s)" %
          (item[0], removed, item[1]))

  def test_removed_list_item_is_gone_from_tree(self):
    for b in ["steam", "liberty", "california-lager", "porter", "ipa",
              "foghorn"]:
      self.yang_obj.container.t4.add(b)

    for item in [("steam", 1), ("liberty", 1), ("pygmy-owl", 0)]:
      with self.subTest(item=item):
        path = "/container/t4[keyval=%s]" % item[0]
        try:
          self.yang_obj.container.t4.delete(item[0])
        except KeyError:
          pass
        tree = self.path_helper.get(path)
        self.assertEqual(len(tree), 0, "An element was not correctly removed from the list (%s -> len(%s) = %d)" %
          (item[0], path, len(tree)))

  def test_set_ptr_to_leaflist_typedef(self):
    for city in ["quebec-city", "montreal", "laval", "gatineau"]:
      self.yang_obj.container.t5.append(city)

    for city in [("quebec-city", True), ("montreal", True), ("dallas", False)]:
      with self.subTest(city=city):
        valid = True
        try:
          self.yang_obj.reference.t5_ptr = city[0]
        except ValueError:
          valid = False
        self.assertEqual(valid, city[1], "Reference was incorrectly set for a leaflist (%s not in %s -> %s != %s)" %
          (city[0], str(self.yang_obj.container.t5), valid, city[1]))

  def test_element_exists_in_leaflist_after_adding(self):
    for city in ["vancouver", "burnaby", "surrey", "richmond"]:
      self.yang_obj.container.t5.append(city)

    for city in [("vancouver", True), ("burnaby", True), ("san-francisco", False),
                 ("surrey", True), ("richmond", True)]:
      with self.subTest(city=city):
        tree = self.path_helper.get("/container/t5")
        self.assertEqual(city[0] in tree[0], city[1],
          "Retrieval of a leaf-list element did not return expected result (%s->%s %s)" %
          (city[0], city[0], tree[0]))

  def test_remove_element_from_tree_removes_from_leaflist(self):
    for city in ["vancouver", "burnaby", "surrey", "richmond"]:
      self.yang_obj.container.t5.append(city)

    path = "/container/t5"
    for city in [("vancouver", True), ("burnaby", True), ("san-francisco", False),
                 ("surrey", True), ("richmond", True)]:
      with self.subTest(city=city):
        tree = self.path_helper.get(path)
        removed = True
        try:
          tree[0].remove(city[0])
        except ValueError:
          removed = False
        # Re-retrieve the tree for error display
        tree = self.path_helper.get(path)
        self.assertEqual(removed, city[1],
          "An element was not correctly removed from a leaf-list (%s -> len(%s) = %d)" %
          (city[0], path, len(tree)))


def main():

  t5_typedef_leaflist_add_del(yobj, yhelper)
  t6_typedef_list_add(yobj, yhelper)
  t7_leaflist_of_leafrefs(yobj, yhelper)
  t8_standalone_leaflist_check(yobj, yhelper)
  t9_get_list(yobj, yhelper)


def t5_typedef_leaflist_add_del(yobj, tree=False):

  for a in ["quebec-city", "montreal", "laval", "gatineau"]:
    yobj.container.t5.append(a)

  for tc in [("gatineau", True), ("laval", True), ("new-york-city", False),
             ("quebec-city", True)]:
    path = "/container/t5"
    retr = tree.get(path)
    assert (tc[0] in retr[0]) == tc[1], "Retrieve of a leaf-list element " + \
        "did not return expected result (%s->%s %s)" % (tc[0], tc[1],
            (retr[0]))
    popped_obj = retr[0].pop()
    if popped_obj == tc[0]:
      expected_obj = True
    else:
      expected_obj = False
    assert expected_obj == bool(tc[1]), "Popped object was not the " + \
        "object that was expected (%s != %s)" % (tc[0], popped_obj)
    new_retr = tree.get(path)
    assert (tc[0] in new_retr[0]) is False, "Retrieve of a leaf-list " + \
        "element did not return expected result (%s->%s %s)" % (tc[0], tc[1],
              (new_retr[0]))


def t6_typedef_list_add(yobj, tree):
  for o in ["la-ciboire", "la-chipie", "la-joufflue", "la-matante"]:
    yobj.container.t6.add(o)

  for tc in [("la-ciboire", True), ("la-matante", True), ("heiniken", False)]:
    validref = False
    try:
      yobj.reference.t6_ptr = tc[0]
      validref = True
    except ValueError:
      pass
    assert validref == tc[1], "Reference was incorrectly set for a list" + \
      " (%s not in %s -> %s != %s)" % (tc[0], yobj.container.t6.keys(),
            validref, tc[1])


def t7_leaflist_of_leafrefs(yobj, tree):
  test_list = [("snapshot", True), ("ranger", True), ("trout-slayer", False)]
  for b in test_list:
    if b[1]:
      yobj.container.t7.append(b[0])

  for b in test_list:
    passed = False
    try:
      yobj.reference.t7_ptr.append(b[0])
      passed = True
    except Exception:
      pass

    assert passed == b[1], "A reference to a leaf-list of leafrefs " + \
        "was not correctly set (%s -> %s, expected %s)" % (b[0], passed, b[1])


def t8_standalone_leaflist_check(yobj, tree):
  yobj.standalone.ll.append(1)

  x = tree.get("/standalone/ll")
  assert x[0][0] == 1, "leaf-list was not as expected"

  yobj.standalone.l.add(1)
  x = tree.get("/standalone/l")
  assert x[0].x == 1, "list key was not as expected"

  yobj.standalone.ref = 1
  assert yobj.standalone.ref._referenced_object == 1, "reference was not correct"


def t9_get_list(yobj, tree):
  list_l = tree.get_list("/standalone/l")
  assert list_l._yang_name == "l", "Did not retrieve correct attribute for list"
  assert list_l._is_container == "list", "Did not retrieve a list for the list"


if __name__ == '__main__':
  unittest.main()
