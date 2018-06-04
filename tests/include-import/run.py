#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class IncludeImportTests(PyangBindTestCase):
    yang_files = ["include-import.yang"]

    def setUp(self):
        self.yang_obj = self.bindings.include_import()

    def test_all_the_things_build(self):
        """This test intentionally left blank."""
        pass


if __name__ == "__main__":
    unittest.main()
