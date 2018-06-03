#!/usr/bin/env python

from __future__ import print_function

from pyangbind.lib.xpathhelper import XPathError, YANGPathHelper

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestObject(object):

    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name


class PathHelperBaseTests(unittest.TestCase):

    def setUp(self):
        self.tree = YANGPathHelper()

    def test_get_returns_same_number_of_objects_as_registered(self):
        obj = TestObject("testobj")
        self.tree.register(["obj_one"], obj)
        self.assertEqual(len(self.tree.get(["obj_one"])), 1)

    def test_get_returns_objects_of_same_class_as_registered(self):
        obj = TestObject("testobj")
        self.tree.register(["obj_one"], obj)
        self.assertIsInstance(self.tree.get(["obj_one"])[0], TestObject)

    def test_get_returns_objects_with_same_attributes_as_registered(self):
        obj = TestObject("testobj")
        self.tree.register(["obj_one"], obj)
        self.assertEqual(self.tree.get(["obj_one"])[0].name(), "testobj")

    def test_get_non_existent_path_returns_nothing(self):
        self.assertEqual(len(self.tree.get("/a/non-existent/path")), 0)

    def test_register_invalid_path_raises_exception(self):
        with self.assertRaises(XPathError):
            self.tree.register("an-invalid-path-name", TestObject("invalid"))

    def test_retrieve_object_at_bottom_of_hierarchy_returns_single_object(self):
        self.tree.register(["node0"], TestObject(0))
        self.tree.register(["node0", "node1"], TestObject(1))
        self.tree.register(["node0", "node1", "node2"], TestObject(2))
        self.assertEqual(len(self.tree.get("/node0/node1/node2")), 1)

    def test_retrieve_object_at_bottom_of_hierarchy_has_proper_name(self):
        self.tree.register(["node0"], TestObject(0))
        self.tree.register(["node0", "node1"], TestObject(1))
        self.tree.register(["node0", "node1", "node2"], TestObject(2))
        self.assertEqual(self.tree.get("/node0/node1/node2")[0].name(), 2)

    def test_register_object_with_attribute(self):
        self.tree.register(["container"], TestObject("container"))
        allowed = True
        try:
            self.tree.register(["container", "foo[id=0]"], TestObject("bar"))
        except Exception:
            allowed = False
        self.assertTrue(allowed)

    def test_retrieve_object_by_attribute_returns_single_object(self):
        self.tree.register(["container"], TestObject("container"))
        self.tree.register(["container", "foo[id=0]"], TestObject("bar0"))
        self.tree.register(["container", "foo[id=1]"], TestObject("bar1"))
        self.assertEqual(len(self.tree.get("/container/foo[id=0]")), 1)

    def test_get_object_by_attribute_returns_object_of_same_class(self):
        self.tree.register(["container"], TestObject("container"))
        self.tree.register(["container", "foo[id=0]"], TestObject("bar0"))
        self.assertIsInstance(self.tree.get("/container/foo[id=0]")[0], TestObject)

    def test_register_object_with_attribute_various_quoting_styles(self):
        self.tree.register(["container"], TestObject("container"))
        for style in ['"', "'", ""]:
            with self.subTest(style=style):
                allowed = True
                try:
                    self.tree.register(["container", "foo[id={0}42{0}]".format(style)], TestObject(42))
                except Exception:
                    allowed = False
                self.assertTrue(allowed)

    def test_get_object_with_attribute_various_quoting_styles(self):
        self.tree.register(["container"], TestObject("container"))
        self.tree.register(["container", "foo[id=42]"], TestObject("bar42"))
        for style in ['"', "'", ""]:
            with self.subTest(style=style):
                obj = self.tree.get("/container/foo[id={0}42{0}]".format(style))[0]
                self.assertEqual(obj.name(), "bar42")


if __name__ == "__main__":
    unittest.main()
