#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class PyangbindSubmoduleTests(PyangBindTestCase):
    yang_files = ["mod-a.yang"]
    pyang_flags = ["--use-extmethods"]

    def setUp(self):
        self.mod_a = self.bindings.mod_a()

    def test_001_check_correct_import(self):
        self.assertTrue(hasattr(self.mod_a, "a"))
        self.assertTrue(hasattr(self.mod_a.a, "b"))

    def test_002_identity_in_submodule(self):
        self.assertTrue(hasattr(self.mod_a, "q"))
        self.assertTrue(hasattr(self.mod_a.q, "idref"))

    def test_assign_idref(self):
        passed = True
        try:
            self.mod_a.q.idref = "j"
        except ValueError:
            passed = False

        self.assertTrue(passed)


if __name__ == "__main__":
    unittest.main()
