#!/usr/bin/env python

import os, sys, getopt

TESTNAME="string"

# generate bindings in this folder

def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError as e:
    print str(e)
    sys.exit(127)

  k = False
  for o, a in opts:
    if o in ["-k", "--keepfiles"]:
      k = True

  this_dir = os.path.dirname(os.path.realpath(__file__))
  os.system("/Users/rjs/Code/pyangbind/bin/pyang --plugindir /Users/rjs/Code/pyangbind/btplugin -f bt -o %s/bindings.py %s/%s.yang" % (this_dir, this_dir, TESTNAME))

  from bindings import string
  test_instance = string()
  assert hasattr(test_instance, "string_container"), \
        "string_container does not exist"
  assert hasattr(test_instance.string_container, \
        "string_leaf"), "string_leaf does not exist"
  assert hasattr(test_instance.string_container, "string_default_leaf"), \
        "string_default_leaf does not exist"
  assert test_instance.string_container.string_leaf.yang_set() == False, \
        "string_leaf erroneously set to changed (value: %s)" % test_instance.string_container.string_leaf.yang_set()
  test_instance.string_container.string_leaf = "TestValue"
  assert test_instance.string_container.string_leaf == "TestValue", \
        "string_leaf not set correctly (value: %s)" % test_instance.string_container.string_leaf
  assert test_instance.string_container.string_leaf.yang_set() == True, \
        "string_leaf did not change to changed (value: %s)" % test_instance.string_container.string_leaf.yang_set()
  test_instance.string_container.string_leaf += "Addition"
  assert test_instance.string_container.string_leaf == "TestValueAddition", \
        "string_leaf did not have correct addition (value: %s)" % test_instance.string_container.string_leaf

  assert test_instance.string_container.string_default_leaf == "", \
        "string_default_leaf did not have the correct empty default value (value: %s)" % test_instance.string_container.string_default_leaf
  assert test_instance.string_container.string_default_leaf._default == "string", \
        "string_default_leaf did not have the correct hidden default value (value: %s)" % test_instance.string_container.string_default_leaf._default
  assert test_instance.string_container.string_default_leaf.yang_set() == False, \
        "string_default_leaf erroneously reports having been changed (value: %s)" % tesT_instance.string_container.string_default_leaf.yang_set()

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()