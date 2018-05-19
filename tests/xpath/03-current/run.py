#!/usr/bin/env python
import unittest

from pyangbind.lib.xpathhelper import YANGPathHelper
from tests.base import PyangBindTestCase


class XPathCurrentTests(PyangBindTestCase):
    yang_files = ["current-tc03.yang"]
    pyang_flags = ["--use-xpathhelper"]

    def setUp(self):
        self.path_helper = YANGPathHelper()
        self.yang_obj = self.bindings.current_tc03(path_helper=self.path_helper)
        for i in [(1, 2), (3, 4), (5, 6)]:
            self.yang_obj.src_list.add("%s %s" % i)
        self.yang_obj.referencing_list.add(1)
        self.yang_obj.referencing_list[1].source_val = "1"
        self.yang_obj.referencing_list[1].reference = "2"

    def test_referencing_list_source_val(self):
        self.assertEqual(self.yang_obj.referencing_list[1].source_val, "1")

    def test_referencing_list_reference(self):
        self.assertEqual(str(self.yang_obj.referencing_list[1].reference), "2")

    def test_src_list_referenced(self):
        self.assertEqual(self.yang_obj.src_list["1 2"].referenced, "1")

    def test_src_list_value(self):
        self.assertEqual(self.yang_obj.src_list["1 2"].value, "2")


if __name__ == "__main__":
    unittest.main()
