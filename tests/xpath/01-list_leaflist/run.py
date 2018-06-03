#!/usr/bin/env python

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from pyangbind.lib.xpathhelper import YANGPathHelper
from tests.base import PyangBindTestCase


class XPathListLeaflistTests(PyangBindTestCase):
    yang_files = ["list-tc01.yang"]
    pyang_flags = ["--use-xpathhelper"]

    def setUp(self):
        self.path_helper = YANGPathHelper()
        self.instance = self.bindings.list_tc01(path_helper=self.path_helper)

    def test_leaflist_leafref_with_require_instance_true(self):
        for fish in ["mackerel", "trout", "haddock", "flounder"]:
            self.instance.container.t1.append(fish)
        for (fish, valid) in [("mackerel", True), ("haddock", True), ("minnow", False)]:
            with self.subTest(fish=fish, valid=valid):
                allowed = True
                try:
                    self.instance.reference.t1_ptr = fish
                except ValueError:
                    allowed = False
                self.assertEqual(valid, allowed)

    def test_leaflist_leafref_with_require_instance_false(self):
        for fish in ["mackerel", "trout", "haddock", "flounder"]:
            self.instance.container.t1.append(fish)
        for (fish, exists) in [("flounder", True), ("minnow", False)]:
            with self.subTest(fish=fish, exists=exists):
                allowed = True
                try:
                    self.instance.reference.t1_ptr_noexist = fish
                except ValueError:
                    allowed = False
                self.assertTrue(allowed)

    def test_list_leafref_with_require_instance_true(self):
        for animal in ["kangaroo", "wallaby", "koala", "dingo"]:
            self.instance.container.t2.add(animal)

        for (animal, valid) in [("kangaroo", True), ("koala", True), ("wombat", False)]:
            with self.subTest(animal=animal, valid=valid):
                allowed = True
                try:
                    self.instance.reference.t2_ptr = animal
                except ValueError:
                    allowed = False
                self.assertEqual(valid, allowed)

    def test_get_leaflist_with_xpath_helper_returns_single_element(self):
        for beer in ["oatmeal-stout", "amber-ale", "pale-ale", "pils", "ipa", "session-ipa"]:
            self.instance.container.t3.append(beer)

        self.assertEqual(len(self.path_helper.get("/container/t3")), 1)

    def test_find_elements_of_leaflist(self):
        for beer in ["oatmeal-stout", "amber-ale", "pale-ale", "pils", "ipa", "session-ipa"]:
            self.instance.container.t3.append(beer)

        leaflist = self.path_helper.get("/container/t3")[0]
        for (beer, valid) in [("session-ipa", True), ("amber-ale", True), ("moose-drool", False)]:
            with self.subTest(beer=beer, valid=valid):
                found = True
                try:
                    leaflist.index(beer)
                except ValueError:
                    found = False
                self.assertEqual(valid, found)

    def test_remove_elements_from_leaflist(self):
        for beer in ["oatmeal-stout", "amber-ale", "pale-ale", "pils", "ipa", "session-ipa"]:
            self.instance.container.t3.append(beer)

        for (beer, valid) in [("session-ipa", True), ("amber-ale", True), ("moose-drool", False)]:
            with self.subTest(beer=beer, valid=valid):
                removed = True
                try:
                    self.instance.container.t3.remove(beer)
                except ValueError:
                    removed = False
                self.assertEqual(removed, valid)

    def test_xpath_helper_gets_updated_leaflist_after_removing_items(self):
        for beer in ["oatmeal-stout", "amber-ale", "pale-ale", "pils", "ipa", "session-ipa"]:
            self.instance.container.t3.append(beer)
        retr = self.path_helper.get("/container/t3")  # Retrieve before to get the old value

        for beer in ["session-ipa", "amber-ale"]:
            self.instance.container.t3.remove(beer)
        retr = self.path_helper.get("/container/t3")

        for beer in ["session-ipa", "amber-ale", "moose-drool"]:
            with self.subTest(beer=beer), self.assertRaises(ValueError):
                retr[0].index(beer)

    def test_get_list_item_with_xpath_helper_returns_single_element(self):
        for beer in ["steam", "liberty", "california-lager", "porter", "ipa", "foghorn"]:
            self.instance.container.t4.add(beer)

        for (beer, exists) in [("steam", 1), ("liberty", 1), ("pygmy-owl", 0)]:
            with self.subTest(beer=beer, exists=exists):
                retr = self.path_helper.get("/container/t4[keyval=%s]" % beer)
                self.assertEqual(len(retr), exists)

    def test_remove_elements_from_list(self):
        for beer in ["steam", "liberty", "california-lager", "porter", "ipa", "foghorn"]:
            self.instance.container.t4.add(beer)

        for (beer, valid) in [("steam", True), ("liberty", True), ("pygmy-owl", False)]:
            with self.subTest(beer=beer, valid=valid):
                removed = True
                try:
                    self.instance.container.t4.delete(beer)
                except KeyError:
                    removed = False
                self.assertEqual(removed, valid)

    def test_xpath_helper_gets_updated_list_after_removing_items(self):
        for beer in ["steam", "liberty", "california-lager", "porter", "ipa", "foghorn"]:
            self.instance.container.t4.add(beer)

        for beer in ["steam", "liberty", "pygmy-owl"]:
            with self.subTest(beer=beer):
                path = "/container/t4[keyval=%s]"
                retr = self.path_helper.get(path)
                try:
                    self.instance.container.t4.delete(beer)
                except KeyError:
                    pass
                retr = self.path_helper.get(path)

                self.assertEqual(len(retr), 0)

    def test_typedef_leaflist_with_require_instance_true(self):
        for city in ["quebec-city", "montreal", "laval", "gatineau"]:
            self.instance.container.t5.append(city)

        for (city, valid) in [("quebec-city", True), ("montreal", True), ("dallas", False)]:
            with self.subTest(city=city, valid=valid):
                allowed = True
                try:
                    self.instance.reference.t5_ptr = city
                except ValueError:
                    allowed = False
                self.assertEqual(valid, allowed)

    def test_typedef_list_with_require_instance_true(self):
        for beer in ["la-ciboire", "la-chipie", "la-joufflue", "la-matante"]:
            self.instance.container.t6.add(beer)

        for (beer, valid) in [("la-ciboire", True), ("la-matante", True), ("heiniken", False)]:
            with self.subTest(beer=beer, valid=valid):
                allowed = True
                try:
                    self.instance.reference.t6_ptr = beer
                except ValueError:
                    allowed = False
                self.assertEqual(valid, allowed)

    def test_leaflist_of_leafrefs_with_require_instance_true(self):
        for beer in ["snapshot", "ranger"]:
            self.instance.container.t7.append(beer)

        for (beer, valid) in [("snapshot", True), ("ranger", True), ("trout-slayer", False)]:
            with self.subTest(beer=beer, valid=valid):
                allowed = True
                try:
                    self.instance.reference.t7_ptr.append(beer)
                except ValueError:
                    allowed = False
                self.assertEqual(valid, allowed)

    def test_standalone_leaflist(self):
        self.instance.standalone.ll.append(1)
        retr = self.path_helper.get("/standalone/ll")
        self.assertEqual(retr[0][0], 1)

    def test_standlone_list(self):
        self.instance.standalone.l.add(1)
        retr = self.path_helper.get("/standalone/l")
        self.assertEqual(retr[0].x, 1)

    def test_standalone_ref(self):
        self.instance.standalone.l.add(1)
        self.instance.standalone.ref = 1
        self.assertEqual(self.instance.standalone.ref._referenced_object, 1)

    def test_get_list_retrieves_correct_attribute(self):
        self.assertEqual(self.path_helper.get_list("/standalone/l")._yang_name, "l")

    def test_get_list_returns_correct_type(self):
        self.assertEqual(self.path_helper.get_list("/standalone/l")._is_container, "list")


if __name__ == "__main__":
    unittest.main()
