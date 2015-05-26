#!/usr/bin/env python

import sys
import os

def main():
  t1_add_retr_object_plain()       # check we can store and retrieve a basic object
  t2_add_retr_object_with_attr()   # check we can store and retrieve an object with an attribute
  t3_add_retr_object_hierarchy()   # check we can store and retrieve objects in a hierarchy
  t4_retr_obj_error()              # check we get the right errors back when an object doesn't exist

class TestContainer(object):
  pass

class TestObject(object):
  def __init__(self, name):
    self._name = name
  def name(self):
    return self._name

def t1_add_retr_object_plain(tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()
  obj_one = TestObject("t1_ObjOneTest")
  tree.register("/obj_one", obj_one)
  retr_obj = tree.get("/obj_one")
  assert isinstance(retr_obj, TestObject), ("retrieved object was not the " +
            "correct class")
  assert retr_obj.name() == "t1_ObjOneTest", ("retrieved object had an " +
            "invalid name specified (%s != t1_ObjOneTest)" % retr_obj.name())
  if del_tree:
    del tree

def t2_add_retr_object_with_attr(tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()
  for p in ["/container", "/container/deeper"]:
    tree.register(p, TestContainer())
    for q_style in ["'", '"', ""]:
      for i in range(0,5):
        tree.register("%s[id=%s%d%s]" % (p, q_style, i, q_style,), TestObject("t2_ObjTest%d" % i))
      for q_style in ["'", '"', ""]:
        for j in range(0,5):
          retr_obj = tree.get("%s[id=%s%d%s]" % (p, q_style, j, q_style,))
          assert isinstance(retr_obj, TestObject), ("retrieved object was not " +
                    "the correct class")
          assert retr_obj.name() == "t2_ObjTest%d" % j, ("retrieved object had an " +
                  "invalid name specified (%s != t2_ObjTest%d, q_style=%s)" % (retr_obj.name(), j ,q_style))
  if del_tree:
    del tree

def t3_add_retr_object_hierarchy(tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()
  path = ""
  obj = {}
  for i in range(0,10):
    path += "/node%d" % i
    obj[i] = TestObject(i)
    tree.register(path, obj[i])
  path = ""
  for j in range(0,10):
    path += "/node%d"% j
    retr_obj = tree.get(path)
    assert retr_obj.name() == j, ("retrieved object did not " +
              "have a valid name (%s != %s)" % (j, retr_obj.name()))

def t4_retr_obj_error(tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()

  try:
    tree.get("/a/non-existant/path")
  except KeyError:
    passed = True
  assert passed == True, ("getting a non-existant path should raise KeyError" +
            "but did not!")

  passed = False
  try:
    tree.register("an-invalid-path-name", TestObject("invalid"))
  except XPathError:
    passed = True
  assert passed == True, ("setting an invalid path did not throw an XPathError")

if __name__ == '__main__':
  import_path = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/..")
  sys.path.insert(0, import_path)
  from xpathhelper import YANGPathHelper, XPathError
  main()