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

  pyangpath = os.environ.get('PYANGPATH') if os.environ.get('PYANGPATH') is not None else False
  pyangbindpath = os.environ.get('PYANGBINDPATH') if os.environ.get('PYANGBINDPATH') is not None else False
  assert not pyangpath == False, "could not find path to pyang"
  assert not pyangbindpath == False, "could not resolve pyangbind directory"

  this_dir = os.path.dirname(os.path.realpath(__file__))
  os.system("%s --plugindir %s -f pybind -o %s/bindings.py %s/%s.yang" % (pyangpath, pyangbindpath, this_dir, this_dir, TESTNAME))

  from bindings import string
  test_instance = string()
  assert hasattr(test_instance, "string_container"), \
        "string_container does not exist"

  assert hasattr(test_instance.string_container, \
        "string_leaf"), "string_leaf does not exist"

  assert hasattr(test_instance.string_container, "string_default_leaf"), \
        "string_default_leaf does not exist"

  assert hasattr(test_instance.string_container, "restricted_string"), \
        "restricted_string does not exist"

  assert hasattr(test_instance.string_container, "restricted_string_default"), \
        "restricted_string with default does not exist"

  assert test_instance.string_container.string_leaf._changed() == False, \
        "string_leaf erroneously set to changed (value: %s)" % \
          test_instance.string_container.string_leaf._changed()

  test_instance.string_container.string_leaf = "TestValue"
  assert test_instance.string_container.string_leaf == "TestValue", \
        "string_leaf not set correctly (value: %s)" % \
          test_instance.string_container.string_leaf

  assert test_instance.string_container.string_leaf._changed() == True, \
        "string_leaf did not change to changed (value: %s)" % \
          test_instance.string_container.string_leaf._changed()

  test_instance.string_container.string_leaf += "Addition"
  assert test_instance.string_container.string_leaf == "TestValueAddition", \
        "string_leaf did not have correct addition (value: %s)" % \
          test_instance.string_container.string_leaf

  assert test_instance.string_container.string_default_leaf == "", \
        "string_default_leaf did not have the correct empty default value (value: %s)" % \
          test_instance.string_container.string_default_leaf

  assert test_instance.string_container.string_default_leaf._default == "string", \
        "string_default_leaf did not have the correct hidden default value (value: %s)" % \
          test_instance.string_container.string_default_leaf._default

  assert test_instance.string_container.restricted_string_default._default == "b", \
        "restricted_string_default did not have the correct hidden defualt value (value: %s)" % \
          test_instance.string_container.restricted_string_default

  assert test_instance.string_container.string_default_leaf._changed() == False, \
        "string_default_leaf erroneously reports having been changed (value: %s)" % \
          test_instance.string_container.string_default_leaf._changed()

  test_instance.string_container.restricted_string = "aardvark"
  assert test_instance.string_container.restricted_string == "aardvark", \
        "restricted string was not set to correct value (value: %s)" % \
          test_instance.string_container.restricted_string

  exception_raised = False
  try:
    test_instance.string_container.restricted_string = "bear"
  except ValueError:
    exception_raised = True
    pass
  assert test_instance.string_container.restricted_string == "aardvark", \
        "restricted string was changed in value to invalid (value: %s)" % \
          test_instance.string_container.restricted_string
  assert exception_raised == True, "exception was not raised when invalid value set"

  for tc in [("a", True), ("ab", True), ("abc", False)]:
    try:
      test_instance.string_container.restricted_length_string = tc[0]
      passed = True
    except:
      passed = False
    assert passed == tc[1], "restricted len string was incorrectly set (%s -> %s exp: %s)" \
        % (tc[0], passed, tc[1])


  for tc in [("a", True), ("b", False), ("abc", False)]:
    try:
      test_instance.string_container.restricted_length_and_pattern_string = tc[0]
      passed = True
    except:
      passed = False
    assert passed == tc[1], "restricted len and pattern string was incorrectly set" + \
      "(%s-> %s exp: %s)" % (tc[0], passed, tc[1])

  for tc in [("short", False), ("loooooooong", True)]:
    try:
      test_instance.string_container.restricted_length_string_with_range = tc[0]
      passed = True
    except:
      passed = False
    assert passed == tc[1], "restricted length range string was incorrectly set" + \
      "(%s -> %s exp: %s)" % (tc[0], passed, tc[1])

  for tc in [("short", False), ("loooooooong", True), ("toooooooooolooooooooong", False)]:
    try:
      test_instance.string_container.restricted_length_string_range_two = tc[0]
      passed = True
    except:
      passed = False
    assert passed == tc[1], "restricted length range string two was incorrectly set" + \
      "(%s -> %s exp: %s)" % (tc[0], passed, tc[1])

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
