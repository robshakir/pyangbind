#!/usr/bin/env python
from __future__ import unicode_literals

import unittest

from tests.base import PyangBindTestCase


class ListTests(PyangBindTestCase):
    yang_files = ["list.yang"]
    maxDiff = None

    def setUp(self):
        self.instance = self.bindings.list_()

    def test_list_element_has_zero_members_by_default(self):
        self.assertEqual(len(self.instance.list_container.list_element), 0)

    def test_cant_add_list_item_with_wrong_type(self):
        with self.assertRaises(KeyError):
            self.instance.list_container.list_element.add("wrong-key-type")

    def test_cant_add_list_item_with_wrong_type_by_index(self):
        with self.assertRaises(ValueError):
            self.instance.list_container.list_element[2] = "anInvalidType"

    def test_add_list_item_with_correct_type(self):
        allowed = True
        try:
            self.instance.list_container.list_element.add(1)
        except ValueError:
            allowed = False
        self.assertTrue(allowed)

    def test_look_up_list_element(self):
        self.instance.list_container.list_element.add(1)
        self.assertEqual(self.instance.list_container.list_element[1].keyval, 1)

    def test_list_value_does_not_get_default_value_when_not_set(self):
        self.instance.list_container.list_element.add(1)
        self.assertNotEqual(self.instance.list_container.list_element[1].another_value, "defaultValue")

    def test_set_both_values_in_a_list_item(self):
        self.instance.list_container.list_element.add(2)
        self.instance.list_container.list_element[2].another_value = "aSecondDefaultValue"
        self.assertEqual(
            self.instance.list_container.list_element[2].get(), {"keyval": 2, "another-value": "aSecondDefaultValue"}
        )

    def test_list_get(self):
        self.instance.list_container.list_element.add(1)
        self.instance.list_container.list_element.add(2)
        self.assertEqual(
            self.instance.get(),
            {
                "list-container": {
                    "list-eight": {},
                    "list-seven": {},
                    "list-six": {},
                    "list-five": {},
                    "list-four": {},
                    "list-three": {},
                    "list-two": {},
                    "list-element": {
                        1: {"keyval": 1, "another-value": "defaultValue"},
                        2: {"keyval": 2, "another-value": "defaultValue"},
                    },
                },
                "list-eleven": {},
                "list-ten": {},
                "list-nine": {},
            },
        )

    def test_delete_list_items(self):
        self.instance.list_container.list_element.add(1)
        self.instance.list_container.list_element.add(2)
        del self.instance.list_container.list_element[1]
        del self.instance.list_container.list_element[2]
        self.assertEqual(len(self.instance.list_container.list_element), 0)

    def test_add_list_item_with_restricted_key(self):
        for (animal, valid) in [("aardvark", True), ("bear", False), ("chicken", False)]:
            with self.subTest(animal=animal, valid=valid):
                allowed = True
                try:
                    self.instance.list_container.list_two.add(animal)
                except KeyError:
                    allowed = False
                self.assertEqual(valid, allowed)

    def test_add_list_item_with_key_restricted_by_union_typedef(self):
        for (animal, valid) in [("aardvark", True), ("bear", True), ("chicken", False)]:
            with self.subTest(animal=animal, valid=valid):
                allowed = True
                try:
                    self.instance.list_container.list_three.add(animal)
                except KeyError:
                    allowed = False
                self.assertEqual(valid, allowed)

    def test_add_list_item_with_restricted_key_by_keyword(self):
        for (food, valid) in [("broccoli", False), ("carrot", False), ("avocado", True)]:
            with self.subTest(food=food, valid=valid):
                allowed = True
                try:
                    self.instance.list_container.list_two.add(keyval=food)
                except KeyError:
                    allowed = False
                self.assertEqual(valid, allowed)

    def test_list_item_key_value_is_read_only(self):
        self.instance.list_container.list_element.add(22)
        with self.assertRaises(AttributeError):
            self.instance.list_container.list_element[22].keyval = 14

    def test_adding_items_to_multi_key_list(self):
        for (animal, valid) in [("aardvark 5", True), ("bear 7", True), ("chicken 5", False), ("bird 11", False)]:
            with self.subTest(animal=animal, valid=valid):
                allowed = True
                try:
                    self.instance.list_container.list_four.add(animal)
                except KeyError:
                    allowed = False
                self.assertEqual(valid, allowed)

    def test_ordered_list_maintains_order(self):
        for i in range(1, 10):
            self.instance.list_container.list_five.add(i)

        for (key, match) in zip(list(self.instance.list_container.list_five.keys()), range(1, 10)):
            with self.subTest(key=key, match=match):
                self.assertEqual(key, match)

    def test_cant_add_empty_item_to_list_with_key(self):
        with self.assertRaises(KeyError):
            self.instance.list_container.list_five.add()

    def test_set_value_on_list_item_with_no_key(self):
        leaf = self.instance.list_container.list_six.add()
        self.instance.list_container.list_six[leaf]._set_val(10)
        self.assertEqual(self.instance.list_container.list_six[leaf].val, 10)

    def test_retrieve_compound_key_with_spaces(self):
        self.instance.list_container.list_eight.add(val="value one", additional="value two")
        self.assertEqual(self.instance.list_container.list_eight["value one value two"].val, "value one")

    def test_retrieve_compound_key_with_spaces_using_item(self):
        self.instance.list_container.list_eight.add(val="value one", additional="value two")
        self.assertEqual(
            self.instance.list_container.list_eight._item(val="value one", additional="value two").val, "value one"
        )

    def test_delete_list_item_with_keyword_arguments(self):
        self.instance.list_container.list_eight.add(val="one", additional="ten")
        allowed = True
        try:
            self.instance.list_container.list_eight.delete(val="one", additional="ten")
        except Exception:
            allowed = False
        self.assertTrue(allowed)

    def test_list_item_is_removed_when_deleted(self):
        self.instance.list_container.list_eight.add(val="value one", additional="value two")
        self.instance.list_container.list_eight.add(val="one", additional="ten")
        self.instance.list_container.list_eight.add(val="two", additional="twenty")
        self.instance.list_container.list_eight.delete(val="one", additional="ten")
        self.assertEqual(list(self.instance.list_container.list_eight.keys()), ["value one value two", "two twenty"])

    def test_cant_delete_nonexistent_list_item_by_keywords(self):
        self.instance.list_container.list_eight.add(val="two", additional="twenty")
        with self.assertRaises(KeyError):
            self.instance.list_container.list_eight.delete(val="two", additional="two")

    def test_add_list_item_with_specified_value(self):
        list_class = self.instance.list_container.list_eight._contained_class()
        list_class.val = "three"
        list_class.additional = "forty-two"
        list_class.numeric = -42

        allowed = True
        try:
            self.instance.list_container.list_eight.add(
                val=list_class.val, additional=list_class.additional, _v=list_class
            )
        except Exception:
            allowed = False
        self.assertTrue(allowed)

    def test_retrieve_list_item_which_was_set_with_v(self):
        list_class = self.instance.list_container.list_eight._contained_class()
        list_class.val = "three"
        list_class.additional = "forty-two"
        list_class.numeric = -42
        self.instance.list_container.list_eight.add(
            val=list_class.val, additional=list_class.additional, _v=list_class
        )
        self.assertEqual(self.instance.list_container.list_eight["three forty-two"].numeric, -42)

    def test_retrieve_list_element_with_value_set_by_setitem(self):
        list_class = self.instance.list_container.list_eight._contained_class()
        list_class.val = "four"
        list_class.additional = "forty-four"
        list_class.numeric = 44
        self.instance.list_container.list_eight["four forty-four"] = list_class
        self.assertEqual(self.instance.list_container.list_eight["four forty-four"].numeric, 44)

    def test_retrieve_list_element_with_value_set_by_setitem_using_named_getitem(self):
        list_class = self.instance.list_container.list_eight._contained_class()
        list_class.val = "four"
        list_class.additional = "forty-four"
        list_class.numeric = 44
        self.instance.list_container.list_eight["four forty-four"] = list_class
        self.assertEqual(
            self.instance.list_container.list_eight._item(val="four", additional="forty-four").numeric, 44
        )

    def test_cant_set_key_on_already_instantiated_list_item(self):
        list_class = self.instance.list_container.list_eight._contained_class()
        list_class.val = "four"
        list_class.additional = "forty-four"
        list_class.numeric = 44
        self.instance.list_container.list_eight["four forty-four"] = list_class
        with self.assertRaises(AttributeError):
            self.instance.list_container.list_eight["four forty-four"].val = "ten"

    def test_append_new_list_item(self):
        item = self.instance.list_nine._new_item()
        item.kv = 13
        item.lv = "thirteen"
        self.instance.list_nine.append(item)
        self.assertEqual(self.instance.list_nine[13].lv, "thirteen")

    def test_list_append_new_items_updates_keys(self):
        for (key, val) in [(13, "thirteen"), ("fourteen", "14")]:
            item = self.instance.list_nine._new_item()
            item.kv = key
            item.lv = val
            self.instance.list_nine.append(item)
        self.assertEqual(list(self.instance.list_nine.keys()), [13, "fourteen"])

    def test_append_new_list_item_with_compound_key(self):
        item = self.instance.list_ten._new_item()
        item.kv = 12
        item.kvtwo = 13
        item.lv = "THIRTEEN"
        self.instance.list_ten.append(item)
        self.assertEqual(self.instance.list_ten["12 13"].lv, "THIRTEEN")

    def test_list_append_new_items_with_compound_keys_updates_keys(self):
        for (key1, key2, val) in [(12, 13, "THIRTEEN"), (13, 14, "FOURTEEN")]:
            item = self.instance.list_ten._new_item()
            item.kv = key1
            item.kvtwo = key2
            item.lv = val
            self.instance.list_ten.append(item)
        self.assertEqual(list(self.instance.list_ten.keys()), ["12 13", "13 14"])

    def test_append_new_list_item_with_identityref(self):
        item = self.instance.list_eleven._new_item()
        item.kv = 1
        item.number = "ONE"
        self.instance.list_eleven.append(item)
        self.assertEqual(self.instance.list_eleven[1].number, "ONE")

    def test_append_new_list_item_with_identityref_doesnt_set_unchanged_elements(self):
        item = self.instance.list_eleven._new_item()
        item.kv = 1
        self.instance.list_eleven.append(item)
        self.assertEqual(self.instance.list_eleven[1].number, "")

    def test_cant_set_nonexistent_item(self):
        item = self.instance.list_eleven._new_item()
        item.kv = 1
        item.number = "ONE"
        self.instance.list_eleven.append(item)
        with self.assertRaises(AttributeError):
            self.instance.list_eleven[1].nonexistent = False


if __name__ == "__main__":
    unittest.main()
