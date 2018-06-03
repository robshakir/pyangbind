#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class ConfigFalseTests(PyangBindTestCase):
    yang_files = ["config-false.yang"]

    def setUp(self):
        self.test_instance = self.bindings.config_false()

    def test_container_is_configurable_by_default(self):
        self.assertTrue(self.test_instance.container._is_config)

    def test_set_configurable_leaf_with_non_configurable_sibling(self):
        allowed = True
        try:
            self.test_instance.container.subone.a_leaf = 1
        except AttributeError:
            allowed = False
        self.assertTrue(allowed)

    def test_leaf_is_configurable_by_default(self):
        self.assertTrue(self.test_instance.container.subone.a_leaf._is_config)

    def test_set_non_configurable_leaf(self):
        allowed = True
        try:
            self.test_instance.container.subone.d_leaf = 1
        except AttributeError:
            allowed = False
        self.assertFalse(allowed)

    def test_leaf_reports_not_configurable_with_config_false(self):
        self.assertFalse(self.test_instance.container.subone.d_leaf._is_config)

    def test_set_leaf_in_non_configurable_container(self):
        allowed = True
        try:
            self.test_instance.container.subtwo.b_leaf = 1
        except AttributeError:
            allowed = False
        self.assertFalse(allowed)

    def test_leaf_in_non_configurable_container_reports_not_configurable(self):
        self.assertFalse(self.test_instance.container.subtwo.b_leaf._is_config)

    def test_set_leaf_in_sub_container_of_non_configurable_container(self):
        allowed = True
        try:
            self.test_instance.container.subtwo.subsubtwo.c_leaf = 1
        except AttributeError:
            allowed = False
        self.assertFalse(allowed)

    def test_leaf_in_sub_container_of_non_configurable_container_reports_not_configurable(self):
        self.assertFalse(self.test_instance.container.subtwo.subsubtwo.c_leaf._is_config)


if __name__ == "__main__":
    unittest.main()
