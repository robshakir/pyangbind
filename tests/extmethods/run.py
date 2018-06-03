#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class extmethodcls(object):

    def commit(self, *args, **kwargs):
        return "COMMIT_CALLED"

    def presave(self, *args, **kwargs):
        return "PRESAVE_CALLED"

    def postsave(self, *args, **kwargs):
        return "POSTSAVE_CALLED"

    def oam_check(self, *args, **kwargs):
        return "OAM_CHECK_CALLED"

    def echo(self, *args, **kwargs):
        return {"args": args, "kwargs": kwargs}


class ExtMethodsTests(PyangBindTestCase):
    yang_files = ["extmethods.yang"]
    pyang_flags = ["--use-extmethods"]

    def setUp(self):
        self.instance = self.bindings.extmethods(extmethods={"/item/one": extmethodcls()})

    def test_extmethods_get_created_on_leafs(self):
        for (method_name, valid) in [
            ("commit", True),
            ("presave", True),
            ("postsave", True),
            ("oam_check", True),
            ("doesnotexist", False),
        ]:
            with self.subTest(method_name=method_name, valid=valid):
                method = getattr(self.instance.item.one, "_%s" % method_name, None)
                self.assertEqual((method is not None), valid)

    def test_extmethods_return_expected_values(self):
        for (method_name, retval) in [
            ("commit", "COMMIT_CALLED"),
            ("presave", "PRESAVE_CALLED"),
            ("postsave", "POSTSAVE_CALLED"),
            ("oam_check", "OAM_CHECK_CALLED"),
        ]:
            with self.subTest(method_name=method_name, retval=retval):
                method = getattr(self.instance.item.one, "_%s" % method_name, None)
                self.assertEqual(method(), retval)

    def test_args_and_kwargs_pass_to_extmethods_properly(self):
        expected_return = {"args": ("one",), "kwargs": {"caller": ["item", "one"], "two": 2, "path_helper": False}}
        self.assertEqual(self.instance.item.one._echo("one", two=2), expected_return)

    def test_kwargs_passed_to_extmethods_do_not_set_invalid_attributes(self):
        self.instance.item.one._echo("one", two=2)
        with self.assertRaises(AttributeError):
            self.instance.item.two


if __name__ == "__main__":
    unittest.main()
