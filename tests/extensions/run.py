#!/usr/bin/env python
from __future__ import unicode_literals

import unittest

from tests.base import PyangBindTestCase


class ExtensionsTests(PyangBindTestCase):
    yang_files = ["extensions.yang"]
    pyang_flags = ["--interesting-extension=extdef", "--interesting-extension=extdef-two"]
    maxDiff = None

    def setUp(self):
        self.ext_obj = self.bindings.extensions()

    def test_extensions_get_added_to_container(self):
        self.assertEqual(
            self.ext_obj.test._extensions(),
            {"extdef": {"extension-one": "version"}},
            "Did not extract extensions correctly from container object (%s)" % self.ext_obj.test._extensions(),
        )

    def test_extensions_are_not_added_to_leaf_with_none_specified(self):
        self.assertIsNone(
            self.ext_obj.test.one._extensions(),
            "Incorrectly found extensions for a leaf with none specified (%s)" % self.ext_obj.test.one._extensions(),
        )

    def test_extensions_are_not_added_to_container_with_none_specified(self):
        self.assertIsNone(
            self.ext_obj.test_two._extensions(),
            "Incorrectly found extensions for a container with none specified (%s)"
            % self.ext_obj.test_two._extensions(),
        )

    def test_extensions_get_added_to_leaf(self):
        self.assertEqual(
            self.ext_obj.test_two.two._extensions(),
            {"extdef": {"extension-two": "value"}},
            "Did not extract extensions correctly for a leaf (%s)" % self.ext_obj.test_two.two._extensions(),
        )

    def test_extensions_get_added_to_list(self):
        self.assertEqual(
            self.ext_obj.l._extensions(),
            {"extdef": {"extension-two": "from-list"}},
            "Did not extract extensions correctly for a list (%s)" % self.ext_obj.l._extensions(),
        )

    def test_extensions_get_added_to_list_member(self):
        x = self.ext_obj.l.add(1)
        self.assertEqual(
            x._extensions(),
            {"extdef": {"extension-two": "from-list"}},
            "Did not extract extensions correctly for list member (%s)" % x._extensions(),
        )

    def test_proper_extensions_get_added_to_list_leaf(self):
        extensions = {
            "k": {"extdef": {"extension-one": "from-leaf", "extension-two": "from-leaf"}},
            "q": {"extdef": {"extension-two": "from-q"}, "extdef-two": {"extension-three": "from-q"}},
        }
        x = self.ext_obj.l.add(1)
        for leaf in extensions:
            with self.subTest(leaf=leaf):
                leaf_exts = getattr(x, leaf)._extensions()
                self.assertEqual(leaf_exts, extensions[leaf])


if __name__ == "__main__":
    unittest.main()
