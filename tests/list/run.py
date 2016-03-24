#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "list"


# generate bindings in this folder
def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError as e:
    print str(e)
    sys.exit(127)

  keepfiles = False
  for o, a in opts:
    if o in ["-k", "--keepfiles"]:
      keepfiles = True

  pythonpath = os.environ.get("PATH_TO_PYBIND_TEST_PYTHON") if \
                os.environ.get('PATH_TO_PYBIND_TEST_PYTHON') is not None \
                  else sys.executable
  pyangpath = os.environ.get('PYANGPATH') if \
                os.environ.get('PYANGPATH') is not None else False
  pyangbindpath = os.environ.get('PYANGBINDPATH') if \
                os.environ.get('PYANGBINDPATH') is not None else False
  assert pyangpath is not False, "could not find path to pyang"
  assert pyangbindpath is not False, "could not resolve pyangbind directory"

  this_dir = os.path.dirname(os.path.realpath(__file__))

  cmd = "%s " % pythonpath
  cmd += "%s --plugindir %s/pyangbind/plugin" % (pyangpath, pyangbindpath)
  cmd += " -f pybind -o %s/bindings.py" % this_dir
  cmd += " -p %s" % this_dir
  cmd += " %s/%s.yang" % (this_dir, TESTNAME)
  os.system(cmd)

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

  for i in test_instance.list_container.list_element.keys():
    passed = True
    try:
      test_instance.list_container.list_element[i]
    except:
      passed = False
    assert passed is True, "could not look up a list element using the " + \
        " type it was cast to"

  assert test_instance.list_container.list_element[1].keyval == 1, \
    "getitem using a non-cast type did not work"

  assert test_instance.list_container.list_element[1].keyval == 1, \
    "keyvalue is not set as per list key by default"

  assert (not test_instance.list_container.list_element[1].another_value ==
     "defaultValue"), \
          "list value is equal to default value without being set"

  test_instance.list_container.list_element.add(2)
  test_instance.list_container.list_element[2].another_value == \
      "aSecondDefaultValue"

  assert test_instance.get() == \
    {'list-container': {'list-eight': {}, 'list-seven': {},
        'list-six': {}, 'list-five': {},
        'list-two': {}, 'list-three': {}, 'list-four': {},
        'list-element': {1: {'keyval': 1, 'another-value': 'defaultValue'},
        2: {'keyval': 2, 'another-value': 'defaultValue'}}},
        'list-nine': {}, 'list-ten': {}}, \
    "incorrect get() output returned: %s" % test_instance.get()
  del test_instance.list_container.list_element[2]

  test_instance.list_container.list_element[1].another_value = "aTestValue"
  assert test_instance.list_container.list_element[1].another_value == \
      "aTestValue", \
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
        assert False, \
            "invalid item added to a list with a restricted key, %s" % i
    try:
      test_instance.list_container.list_three.add(i)
    except KeyError:
      if i not in ["chicken"]:
        assert False, \
            "invalid item added to a list with a union restricted" + \
            " key, %s" % i

  for i in ["broccoli", "carrot", "avocado"]:
    try:
      test_instance.list_container.list_two.add(keyval=i)
    except KeyError:
      assert i in ["broccoli", "carrot"], "invalid item added to " + \
          "list using keyword add (%s)" % i

  passed = False
  test_instance.list_container.list_element.add(22)
  try:
    test_instance.list_container.list_element[22].keyval = 14
  except AttributeError:
    passed = True
  assert passed, \
    "keyvalue of a list was read-write when it should be read-only"

  for i in [("aardvark 5", True), ("bear 7", True), ("chicken 5", False),
            ("bird 11", False)]:
    try:
      test_instance.list_container.list_four.add(i[0])
      added = True
    except KeyError:
      added = False
    assert added == i[1], \
        "list element erroneously added to multiple-key list (%s,%s)" % i

  for i in range(1, 10):
    test_instance.list_container.list_five.add(i)

  for i, j in zip(test_instance.list_container.list_five.keys(), range(1, 10)):
    assert i == j, "ordered list had incorrect key ordering (%d != %d)" \
        % (i, j)

  passed = False
  try:
    test_instance.list_container.list_five.add()
  except KeyError:
    passed = True
  assert passed is True, \
      "a list with a key value allowed an key-less value to be set"

  x = test_instance.list_container.list_six.add()
  test_instance.list_container.list_six[x]._set_val(10)

  assert test_instance.list_container.list_six[x].val == 10, \
    "a key-less list did not have the correct value set (%s %d != 10)" % \
      (x, test_instance.list_container.list_six[x].val)

  y = test_instance.list_container.list_eight.add(val="value one",
          additional="value two")
  assert \
    test_instance.list_container.list_eight["value one value two"].val == \
      "value one", "Cannot retrieve a compound key with spaces in strkey " + \
        "%s != 'value one'" % \
          test_instance.list_container.list_eight["value one value two"].val

  assert \
    test_instance.list_container.list_eight._item(val="value one",
      additional="value two").val == "value one", \
        "Cannot retrieve a compound key with spaces in strkey using _item" + \
        "%s != 'value one'" % \
          test_instance.list_container.list_eight["value one value two"].val

  test_instance.list_container.list_eight.add(val="one", additional="ten")
  test_instance.list_container.list_eight.add(val="two", additional="twenty")

  err = None
  try:
    test_instance.list_container.list_eight.delete(val="one", additional="ten")
  except Exception as e:
    err = e
  assert err is None, "Could not remove entry from list with keyword arguments"

  assert test_instance.list_container.list_eight.keys() == ['two twenty',
      'value one value two'], "Entry remained in list after delete()"

  err = False
  try:
    test_instance.list_container.list_eight.delete(val="two", additional="two")
  except KeyError:
    err = True
  assert err is True, "list removal with kwarg succeeded on nonexistent entry"

  leight = test_instance.list_container.list_eight._contained_class()
  leight.val = "three"
  leight.additional = "forty-two"
  leight.numeric = -42
  passed = True
  try:
    test_instance.list_container.list_eight.add(val=leight.val,
          additional=leight.additional, _v=leight)
  except Exception as e:
    passed = False
  assert passed is True, "list add with a specified value was not " + \
    "successful, exception raised was: %s" % e

  passed = True
  try:
    v = test_instance.list_container.list_eight["three forty-two"]
  except Exception as e:
    passed = False
  assert passed is True, "list retrieve using getitem was not " + \
    "succesful for an item that was set with _v"

  assert \
    test_instance.list_container.list_eight["three forty-two"].numeric \
      == -42, "Value set with _v is not correct: %d != -42" % \
        test_instance.list_container.list_eight["three forty-two"].numeric

  leight_two = test_instance.list_container.list_eight._contained_class()
  leight_two.val = "four"
  leight_two.additional = "forty-four"
  leight_two.numeric = 44
  test_instance.list_container.list_eight["four forty-four"] = leight_two

  passed = True
  try:
    v = test_instance.list_container.list_eight["four forty-four"]
  except KeyError:
    passed = False
  assert passed is True, "Could not retrieve element with value set by " + \
      "setitem"

  assert test_instance.list_container.list_eight._item(val="four",
            additional="forty-four").numeric == 44, \
              "Item value set by setitem using named getitem not valid"

  passed = False
  try:
    test_instance.list_container.list_eight["four forty-four"].val = "ten"
  except AttributeError:
    passed = True

  assert passed is True, "Set the key inside an instantiated list without " +\
    "this being a load operation, error"


  keys = []
  for v in [(13, "thirteen"), (u"fourteen", "14")]:
    item = test_instance.list_nine._new_item()
    item.kv = v[0]
    item.lv = v[1]
    test_instance.list_nine.append(item)
    keys.append(v[0])
    assert test_instance.list_nine[v[0]].lv == v[1], "When appending to " + \
      "list, value was not set correctly: %s != %s" % \
        (test_instance.list_nine[v[0]].lv, v[1])

  passed = True
  for k in keys:
    if not k in test_instance.list_nine.keys():
      passed = False

  assert passed is True, "List keys using " + \
    "_new_item() and append() were not correct: %s != [13, 'fourteen']" % \
      (test_instance.list_nine.keys())

  keys = []
  for v in [(12, 13, "THIRTEEN"), (13, 14, "FOURTEEN")]:
    item = test_instance.list_ten._new_item()
    item.kv = v[0]
    item.kvtwo = v[1]
    item.lv = v[2]
    key = "%s %s" % (v[0], v[1])
    keys.append(key)
    test_instance.list_ten.append(item)

    assert test_instance.list_ten[key].lv == v[2], "When appending to " + \
      "list, value was not set correctly: %s != %s" % \
        (test_instance.list_ten[key].lv, v[2])

  passed = True
  for k in keys:
    if not k in test_instance.list_ten.keys():
      passed = False

  assert passed is True, "List keys using new item, append and a compound" + \
    " key was not valid: %s != ['13 thirteen', '14 fourteen']" % \
      test_instance.list_ten.keys()

  if not keepfiles:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
