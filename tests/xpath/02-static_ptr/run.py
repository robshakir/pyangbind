#!/usr/bin/env python
import unittest

from pyangbind.lib.xpathhelper import YANGPathHelper
from tests.base import PyangBindTestCase


class XPathStaticPtrTests(PyangBindTestCase):
    yang_files = ["ptr-tc02.yang"]
    pyang_flags = ["--use-xpathhelper"]

    def setUp(self):
        self.path_helper = YANGPathHelper()
        self.yang_obj = self.bindings.ptr_tc02(path_helper=self.path_helper)
        for x in range(0, 100):
            self.yang_obj.container.t1a.add("x%s" % x)

    def test_list_key_pointer(self):
        for x in range(0, 100):
            with self.subTest(key=x):
                self.assertEqual(
                    self.yang_obj.container.t1a["x%s" % x].t1c.t1d,
                    "x%s" % x,
                    "list key was not set correctly when acting as a pointer (%s != 'test')"
                    % self.yang_obj.container.t1a["x%s" % x].t1c.t1d,
                )

    def test_list_key_value(self):
        for x in range(0, 100):
            with self.subTest(key=x):
                self.assertEqual(
                    str(self.yang_obj.container.t1a["x%s" % x].t1b),
                    "x%s" % x,
                    "list key pointer was not read correctly (value is %s)"
                    % self.yang_obj.container.t1a["x%s" % x].t1b,
                )


if __name__ == "__main__":
    unittest.main()
