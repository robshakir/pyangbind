#!/usr/bin/env python

import os, sys, getopt

TESTNAME="list"

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
  os.system("/usr/local/bin/pyang --plugindir /Users/rjs/Code/pyangbind -f pybind -o %s/bindings.py %s/%s.yang" % (this_dir, this_dir, TESTNAME))

  from bindings import list_ as l

  import numpy

  test_instance = l()

  assert hasattr(test_instance, "list_container"), \
    "list_container does not exist"

  assert hasattr(test_instance.list_container, "list_element"), \
    "list_element does not exist"

  assert len(test_instance.list_container.list_element) == 0, \
    "list does not have zero members"

  try:
    test_instance.list_container.list_element.add("wrong-key-type")
  except ValueError, m:
    pass
  assert len(test_instance.list_container.list_element) == 0, \
    "list item erroneously added with wrong key type"

  test_instance.list_container.list_element.add(1)
  assert len(test_instance.list_container.list_element) == 1, \
    "list item not added when correct key type used"

  assert test_instance.list_container.list_element[1].keyval == 1, \
    "keyvalue is not set as per list key by default"

  assert (not test_instance.list_container.list_element[1].another_value == "defaultValue"), \
    "list value is equal to default value without being set"

  test_instance.list_container.list_element.add(2)
  test_instance.list_container.list_element[2].another_value == "aSecondDefaultValue"

  print test_instance.get()
  print test_instance.get(filter=True)
  assert test_instance.get() == \
    {'list-container': {'list-two': {}, 'list-three': {}, 'list-four': {},
    'list-element': {1: {'keyval': 1, 'another-value': 'defaultValue'},
    2: {'keyval': 2, 'another-value': 'defaultValue'}}}}, \
    "incorrect get() output returned: %s" % test_instance.get()
  del test_instance.list_container.list_element[2]

  test_instance.list_container.list_element[1].another_value = "aTestValue"
  assert test_instance.list_container.list_element[1].another_value == "aTestValue", \
    "list value is not set correctly when specified"

  del test_instance.list_container.list_element[1]
  assert len(test_instance.list_container.list_element) == 0, \
    "item was not correctly removed from list when deleted"

  try:
    test_instance.list_container.list_element[2] = "anInvalidType"
  except ValueError, m:
    pass
  assert len(test_instance.list_container.list_element) == 0, \
    "item that was invalid was added to the list"

  # check union keys
  for i in ["aardvark", "bear", "chicken"]:
    try:
      test_instance.list_container.list_two.add(i)
    except:
      if i not in ["bear", "chicken"]:
        assert False, "invalid item added to a list with a restricted key, %s" % i
    try:
      test_instance.list_container.list_three.add(i)
    except:
      if i not in ["chicken"]:
        assert False, "invalid item added to a list with a union restricted key, %s" % i

  passed = True
  try:
    test_instance.list_container.list_element.keyval = 14
  except:
    passed = False
  assert passed, "keyvalue of a list was read-write when it should be read-only"

  for i in [("aardvark 5", True), ("bear 7", True), ("chicken 5", False), ("bird 11",False)]:
    try:
      test_instance.list_container.list_four.add(i[0])
      added = True
    except:
      added = False
    assert added == i[1], "list element erroneously added to multiple-key list (%s,%s)" % i


  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()