#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class ChoicesTests(PyangBindTestCase):
    yang_files = ["choice.yang"]

    def setUp(self):
        self.choice_obj = self.bindings.choice()

    def test_class_has_container(self):
        self.assertTrue(hasattr(self.choice_obj, "container"), "Object does not have container")

    def test_class_has_choice_containers(self):
        for container in ["case_one_container", "case_two_container"]:
            with self.subTest(container=container):
                self.assertTrue(
                    hasattr(self.choice_obj.container, container),
                    "Object does not have choice container %s" % container,
                )

    def test_class_does_not_have_choices_as_attributes(self):
        for choice in ["choice_one", "choice_two", "case_one", "case_two"]:
            with self.subTest(choice=choice):
                self.assertFalse(
                    hasattr(self.choice_obj, choice), "Object has an erroneous choice option, %s" % choice
                )

    def test_case_leaf_default_values(self):
        for leaf in ["case_one", "case_two"]:
            with self.subTest(leaf=leaf):
                container = getattr(self.choice_obj.container, "%s_container" % leaf)
                value = getattr(container, "%s_leaf" % leaf)
                self.assertEqual(value, 0, "Object does not have the correct value for %s_leaf, %s" % (leaf, value))

    def test_set_choice_value(self):
        self.choice_obj.container.case_one_container.case_one_leaf = 42
        self.assertEqual(
            self.choice_obj.container.case_one_container.case_one_leaf,
            42,
            "Object did not specify a value within the choice correctly, %s"
            % self.choice_obj.container.case_one_container.case_one_leaf,
        )

    def test_set_choice_value_doesnt_set_other_choices(self):
        self.choice_obj.container.case_one_container.case_one_leaf = 42
        self.assertEqual(
            self.choice_obj.container.case_two_container.case_two_leaf,
            0,
            "Object erroneously set another value within the choice, %s"
            % self.choice_obj.container.case_two_container.case_two_leaf,
        )

    def test_change_choice_value(self):
        self.choice_obj.container.case_one_container.case_one_leaf = 42
        self.choice_obj.container.case_two_container.case_two_leaf = 42
        self.assertEqual(
            self.choice_obj.container.case_two_container.case_two_leaf,
            42,
            "Object did not allow the other half of the choice field to be specified, %s"
            % self.choice_obj.container.case_two_container.case_two_leaf,
        )

    def test_change_choice_value_resets_other_side(self):
        self.choice_obj.container.case_one_container.case_one_leaf = 42
        self.choice_obj.container.case_two_container.case_two_leaf = 42
        self.assertEqual(
            self.choice_obj.container.case_one_container.case_one_leaf,
            0,
            "Object did not reset the value of the case-one side of the choice, %s"
            % self.choice_obj.container.case_one_container.case_one_leaf,
        )

    def test_add_to_choice_list_leaf(self):
        self.choice_obj.container.case_one_container.user.add("first")
        self.assertEqual(
            self.choice_obj.container.case_one_container.user["first"].username,
            "first",
            "Object has the wrong username for user in case one list",
        )

    def test_change_choice_list_to_other_side(self):
        self.choice_obj.container.case_one_container.user.add("first")
        self.choice_obj.container.case_two_container.user.add("second")
        self.assertEqual(
            self.choice_obj.container.case_two_container.user["second"].username,
            "second",
            "Object has the wrong username for user in case two list",
        )

    def test_change_choice_list_resets_other_side(self):
        self.choice_obj.container.case_one_container.user.add("first")
        self.choice_obj.container.case_two_container.user.add("second")
        self.assertEqual(
            len(self.choice_obj.container.case_one_container.user.keys()),
            0,
            "Adding to the second user list did not remove entries from the first",
        )


if __name__ == "__main__":
    unittest.main()
