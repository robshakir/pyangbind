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
  tree.register(["obj_one"], obj_one)
  retr_obj = tree.get(["obj_one"])
  assert len(retr_obj) == 1, ("retrieved path matched the wrong number of objects (%d != 1)"
    % (len(retr_obj)))
  assert isinstance(retr_obj[0], TestObject), ("retrieved object was not the " +
            "correct class")
  assert retr_obj[0].name() == "t1_ObjOneTest", ("retrieved object had an " +
            "invalid name specified (%s != t1_ObjOneTest)" % retr_obj.name())
  if del_tree:
    del tree

def t2_add_retr_object_with_attr(tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()
  for p in [["container"], ["container", "deeper"]]:
    tree.register(p, TestObject("container"))
    for q_style in ["'", '"', ""]:
      for i in range(0,5):
        tree.register(p+["foo[id=%s%d%s]" % (q_style, i, q_style,)], TestObject("t2_ObjTest%d" % i))
      for q_style in ["'", '"', ""]:
        for j in range(0,5):
          retr_obj = tree.get("%s/foo[id=%s%d%s]" % ("/"+"/".join(p), q_style, j, q_style,))
          assert len(retr_obj) == 1, ("retrieved the wrong number of objects (%d != 1)" % len(retr_obj))
          assert isinstance(retr_obj[0], TestObject), ("retrieved object was not " +
                    "the correct class")
          assert retr_obj[0].name() == "t2_ObjTest%d" % j, ("retrieved object had an " +
                  "invalid name specified (%s != t2_ObjTest%d, q_style=%s)" % (retr_obj.name(), j ,q_style))
  if del_tree:
    del tree

def t3_add_retr_object_hierarchy(tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()
  path = []
  obj = {}
  for i in range(0,10):
    path += ["node%d" % i]
    obj[i] = TestObject(i)
    tree.register(path, obj[i])
  path = ""
  for j in range(0,10):
    path += "/node%d"% j
    retr_obj = tree.get(path)
    assert len(retr_obj) == 1, ("incorrect number of objects retrieved for %s (%d != 1)" %
      (path,len(retr_obj)))
    assert retr_obj[0].name() == j, ("retrieved object did not " +
              "have a valid name (%s != %s)" % (j, retr_obj.name()))

def t4_retr_obj_error(tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()

  retr = tree.get("/a/non-existant/path")

  assert len(retr) == 0, ("getting a non-existant path returned the wrong number" +
            "of objects (%d != 0)" % (len(retr)))

  passed = False
  try:
    tree.register("an-invalid-path-name", TestObject("invalid"))
  except XPathError:
    passed = True
  assert passed == True, ("setting an invalid path did not throw an XPathError")

if __name__ == '__main__':
  import_path = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../../lib")
  sys.path.insert(0, import_path)
  from xpathhelper import YANGPathHelper, XPathError
  main()
