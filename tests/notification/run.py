#!/usr/bin/env python

import unittest

from pyangbind.lib.xpathhelper import YANGPathHelper
from tests.base import PyangBindTestCase


class NotificationTests(PyangBindTestCase):
    yang_files = ["notification.yang"]
    split_class_dir = True
    pyang_flags = ["--use-xpathhelper", "--build-notifications"]

    def setUp(self):
        self.path_helper = YANGPathHelper()

    # Note that these tests need to import from the filesystem rather than using
    #  the bound module, so that they can directly reference the sub-modules
    def test_set_leaf_inside_notification(self):
        from bindings.notification_notification.alert_one import alert_one

        instance = alert_one(path_helper=self.path_helper)
        allowed = True
        try:
            instance.argument = "test"
        except ValueError:
            allowed = False
        self.assertTrue(allowed)

    def test_set_multiple_leafs_inside_notification(self):
        from bindings.notification_notification.alert_two import alert_two

        instance = alert_two(path_helper=self.path_helper)
        allowed = True
        try:
            instance.arg_one = 10
            instance.arg_two = 20
        except ValueError:
            allowed = False
        self.assertTrue(allowed)

    def test_set_leafs_on_a_container_inside_a_notification(self):
        from bindings.notification_notification.alert_three import alert_three

        instance = alert_three(path_helper=self.path_helper)
        allowed = True
        try:
            instance.arguments.arg_one = "test string"
            instance.arguments.arg_two = "test string"
        except ValueError:
            allowed = False
        self.assertTrue(allowed)

    def test_set_leafs_on_multiple_containers_inside_a_notification(self):
        from bindings.notification_notification.alert_four import alert_four

        instance = alert_four(path_helper=self.path_helper)
        allowed = True
        try:
            instance.arguments_one.arg_one = "test string"
            instance.arguments_two.arg_two = "test string"
        except ValueError:
            allowed = False
        self.assertTrue(allowed)

    def test_set_leafref_inside_notification(self):
        from bindings import notification
        from bindings.notification_notification.alert_five import alert_five

        instance = alert_five(path_helper=self.path_helper)
        parent = notification(path_helper=self.path_helper)

        parent.test.reference_target.append("five")

        for (value, valid) in [("five", True), ("fish", False)]:
            with self.subTest(value=value, valid=valid):
                allowed = True
                try:
                    instance.argument = value
                except ValueError:
                    allowed = False
                self.assertEqual(allowed, valid)


if __name__ == "__main__":
    unittest.main()
