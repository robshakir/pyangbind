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

  pyangpath = os.environ.get('PYANGPATH') if os.environ.get('PYANGPATH') is not None else False
  pyangbindpath = os.environ.get('PYANGBINDPATH') if os.environ.get('PYANGBINDPATH') is not None else False
  assert not pyangpath == False, "could not find path to pyang"
  assert not pyangbindpath == False, "could not resolve pyangbind directory"

  this_dir = os.path.dirname(os.path.realpath(__file__))
  os.system("%s --plugindir %s -f pybind -o %s/bindings.py %s/%s.yang" % (pyangpath, pyangbindpath, this_dir, this_dir, TESTNAME))

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
  except KeyError, m:
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

  assert test_instance.get() == \
    {'list-container': {'list-seven': {}, 'list-six': {}, 'list-five': {}, 'list-two': {}, 'list-three': {}, 'list-four': {},
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
    except KeyError:
      if i not in ["bear", "chicken"]:
        assert False, "invalid item added to a list with a restricted key, %s" % i
    try:
      test_instance.list_container.list_three.add(i)
    except KeyError:
      if i not in ["chicken"]:
        assert False, "invalid item added to a list with a union restricted key, %s" % i

  passed = False
  test_instance.list_container.list_element.add(22)
  try:
    test_instance.list_container.list_element[22].keyval = 14
  except AttributeError:
    passed = True
  assert passed, "keyvalue of a list was read-write when it should be read-only"

  for i in [("aardvark 5", True), ("bear 7", True), ("chicken 5", False), ("bird 11",False)]:
    try:
      test_instance.list_container.list_four.add(i[0])
      added = True
    except KeyError:
      added = False
    assert added == i[1], "list element erroneously added to multiple-key list (%s,%s)" % i

  for i in range(1,10):
    test_instance.list_container.list_five.add(i)

  for i,j in zip(test_instance.list_container.list_five.keys(), range(1,10)):
    assert i == j, "ordered list had incorrect key ordering (%d != %d)" % (i,j)

  passed = False
  try:
    test_instance.list_container.list_five.add()
  except KeyError:
    passed = True
  assert passed == True, "a list with a key value allowed an key-less value to be set"

  x = test_instance.list_container.list_six.add()
  test_instance.list_container.list_six[x]._set_val(10)

  assert test_instance.list_container.list_six[x].val == 10, \
    "a key-less list did not have the correct value set (%s %d != 10)" % \
      (x,test_instance.list_container.list_six[x].val)

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
