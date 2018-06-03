#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class NestedContainerTests(PyangBindTestCase):
    yang_files = ["nested.yang"]

    def setUp(self):
        self.nested_obj = self.bindings.nested()

    def test_subcontainer_is_not_changed_by_default(self):
        self.assertFalse(self.nested_obj.container.subcontainer._changed(), "subcontainer was marked to changed")

    def test_container_is_not_changed_by_default(self):
        self.assertFalse(self.nested_obj.container._changed(), "container was marked to changed")

    def test_subcontainer_marked_changed(self):
        self.nested_obj.container.subcontainer.a_leaf = 1
        self.assertTrue(
            self.nested_obj.container.subcontainer._changed(), "subcontainer not marked to changed after change"
        )

    def test_subcontainer_get(self):
        self.nested_obj.container.subcontainer.a_leaf = 1
        self.assertEqual(self.nested_obj.container.subcontainer.get(), {"a-leaf": 1}, "subcontainer get not correct")

    def test_container_get(self):
        self.nested_obj.container.subcontainer.a_leaf = 1
        self.assertEqual(self.nested_obj.container.get(), {"subcontainer": {"a-leaf": 1}}, "container get not correct")

    def test_full_get(self):
        self.nested_obj.container.subcontainer.a_leaf = 1
        self.assertEqual(
            self.nested_obj.get(), {"container": {"subcontainer": {"a-leaf": 1}}}, "instance get not correct"
        )


if __name__ == "__main__":
    unittest.main()
