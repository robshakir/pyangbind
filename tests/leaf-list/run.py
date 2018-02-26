#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "leaflist"


# generate bindings in this folder
def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError as e:
    print(str(e))
    sys.exit(127)

  k = False
  for o, a in opts:
    if o in ["-k", "--keepfiles"]:
      k = True

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

  from bindings import leaflist

  leaflist_instance = leaflist()

  assert hasattr(leaflist_instance, "container") is True, \
    "base container missing"

  assert hasattr(leaflist_instance.container, "leaflist") is True, \
    "leaf-list instance missing"

  assert len(leaflist_instance.container.leaflist) == 0, \
    "length of leaflist was not zero"

  leaflist_instance.container.leaflist.append("itemOne")

  assert len(leaflist_instance.container.leaflist) == 1, \
    "did not succesfully append string to list"

  assert leaflist_instance.container.leaflist[0] == "itemOne", \
    "cannot successfully address an item from the list"

  try:
    leaflist_instance.container.leaflist.append(int(1))
  except ValueError:
    pass

  assert len(leaflist_instance.container.leaflist) == 1, \
    "appended an element to the list erroneously (%s, len %d vs. 1)" % \
      (leaflist_instance.container.leaflist,
        len(leaflist_instance.container.leaflist))

  leaflist_instance.container.leaflist.append("itemTwo")
  assert leaflist_instance.container.leaflist[1] == "itemTwo", \
    "getitem did not return the correct value"

  leaflist_instance.container.leaflist[1] = "indexOne"
  assert leaflist_instance.container.leaflist[1] == "indexOne", \
    "setitem did not set the correct node"

  leaflist_instance.container.leaflist.insert(0, "indexZero")
  assert leaflist_instance.container.leaflist[0] == "indexZero", \
    "incorrectly set index 0 value"
  assert len(leaflist_instance.container.leaflist) == 4, \
    "list item was not added by insert()"

  del leaflist_instance.container.leaflist[0]
  assert len(leaflist_instance.container.leaflist) == 3, \
    "list item not succesfully removed by delitem"

  assert leaflist_instance.get() == \
    {'container': {'leaflist': ['itemOne', 'indexOne', 'itemTwo'],
        'listtwo': [], 'listthree': []}}, \
    "get did not correctly return the dictionary"

  try:
    leaflist_instance.container.leaflist = ["itemOne", "itemTwo"]
  except ValueError:
    pass

  assert leaflist_instance.container.leaflist == ["itemOne", "itemTwo"], \
    "leaflist assignment did not function correctly"

  passed = False
  try:
    leaflist_instance.container.leaflist = [1, 2]
  except ValueError:
    passed = True
  assert passed is True, "an erroneous value was assigned to the list"

  leaflist_instance.container.listtwo.append("a-valid-string")
  assert len(leaflist_instance.container.listtwo) == 1, \
      "restricted leaflist did not function correctly"

  passed = False
  try:
    leaflist_instance.container.listtwo.append("broken-string")
  except ValueError:
    passed = True
  assert passed is True, \
      "an erroneous value was assigned to the list (restricted type)"

  for i in [(1, True), ("fish", True), ([], False)]:
    passed = False
    try:
      leaflist_instance.container.listthree.append(i[0])
      passed = True
    except ValueError:
      pass
    assert passed == i[1], \
        "leaf-list of union type had invalid result (%s != %s for %s)" \
            % (passed, i[1], i[0])

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)


if __name__ == '__main__':
  main()
