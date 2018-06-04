#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class SplitClassesTests(PyangBindTestCase):
    yang_files = ["split-classes.yang"]
    split_class_dir = True

    def setUp(self):
        self.instance = self.bindings.split_classes()

    def test_first_container_name_matches_module_name(self):
        allowed = True
        try:
            self.instance.split_classes.test = "howdy"
        except ValueError:
            allowed = False
        self.assertTrue(allowed)

    def test_hierarchy_with_repeating_name(self):
        allowed = True
        try:
            self.instance.remote.remote.remote.remote = "hi"
        except ValueError:
            allowed = False
        self.assertTrue(allowed)

    def test_add_entry_to_case_one_container(self):
        self.instance.choices.case_one_container.user.add("first")
        self.assertEqual(list(self.instance.choices.case_one_container.user.keys()), ["first"])

    def test_adding_entry_to_other_case_after_first_case(self):
        self.instance.choices.case_one_container.user.add("first")
        self.instance.choices.case_two_container.user.add("second")
        self.assertEqual(list(self.instance.choices.case_two_container.user.keys()), ["second"])

    def test_adding_entry_to_other_case_clears_first_case(self):
        self.instance.choices.case_one_container.user.add("first")
        self.instance.choices.case_two_container.user.add("second")
        self.assertEqual(list(self.instance.choices.case_one_container.user.keys()), [])


if __name__ == "__main__":
    unittest.main()
