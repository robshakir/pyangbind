#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "typedef"


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

  from bindings import typedef
  t = typedef()

  for element in ["string", "integer", "stringdefault", "integerdefault",
                  "new_string", "remote_new_type", "session_dir",
                  "remote_local_type"]:
    assert hasattr(t.container, element), \
        "element %s did not exist within the container" % element

  t.container.string = "hello"
  assert t.container.string == "hello", \
    "incorrect value set for the string container (value: %s)" \
    % t.container.string

  assert t.container.stringdefault._default == "aDefaultValue", \
    "incorrect default value for derived string type with a default " + \
    "(value: %s)" % t.container.stringdefault._default

  assert t.container.new_string._default == "defaultValue", \
    "incorrect default value where derived from typedef (value: %s)" % \
    t.container.new_string._default

  t.container.integer = 1
  assert t.container.integer == 1, \
    "integer value not correctly updated"

  passed = False
  try:
    t.container.integer = 65  # outside of range
  except ValueError:
    passed = True

  assert passed is True, "restricted int from typedef was set to invalid value"

  t.container.remote_new_type = "testString"
  assert t.container.remote_new_type == "testString", \
    "incorrect value for the remote definition (%s)" % \
      t.container.remote_new_type

  t.container.remote_local_type = "testString"
  assert t.container.remote_local_type == "testString", \
    "incorrect value for remote definition which had local definition (%s)" % \
      t.container.remote_local_type

  for i in [("aardvark", True), ("ant", False), ("duck", False)]:
    wset = True
    try:
      t.container.inheritance = i[0]
    except ValueError:
      wset = False
    assert wset == i[1], \
      "inherited pattern was not correctly followed for %s (%s != %s)" \
        % (i[0], i[1], wset)

  for i in [(2, True), (10, False), (1, False)]:
    wset = True
    try:
      t.container.int_inheritance = i[0]
    except ValueError:
      wset = False
    assert wset == i[1], \
      "inherited range was not correctly followed for %s (%s != %s)" \
        % (i[0], i[1], wset)

  for i in [("aardvark", True), ("bear", True), ("chicken", False),
            ("deer", False), ("zebra", True)]:
    try:
      t.container.stacked_union.append(i[0])
      passed = True
    except ValueError:
      passed = False
    assert passed == i[1], \
        "incorrectly dealt with %s when added as a list key (%s != %s)" % \
            (i[0], passed, i[1])

  for i in [("zebra", True), ("yak", False)]:
    try:
      t.container.include_of_include_definition = i[0]
      wset = True
    except ValueError:
      wset = False
    assert wset == i[1], \
      "definition with hybrid typedef across two modules was not set " + \
        "correctly for %s (%s != %s)" % (i[0], i[1], wset)

  for i in [("IDONE", True), ("IDTWO", True), ("IDTHREE", False)]:
    try:
      t.container.identity_one_typedef = i[0]
      wset = True
    except ValueError:
      wset = False
    assert wset == i[1], \
      "definition with a typedef which references an identity was not set " + \
          "correctly for %s (%s != %s)" (i[0], i[1], wset)

  for i in [("aardvark", True), ("bear", True), ("chicken", False),
            ("quail", True), ("zebra", False)]:
    try:
      t.container.union_with_union = i[0]
      wset = True
    except ValueError:
      wset = False
    assert wset == i[1], \
      "definition which was a union including a typedef was not set" + \
          " correctly for %s (%s != %s)" % (i[0], i[1], wset)

  # check that nested typedefs are detected
  passed = None
  try:
    t.container.scoped_leaf = "aardwolf"
    passed = True
  except ValueError:
    passed = False

  assert passed is True, \
      "scoped leaf was not set correctly (%s - %s != True)" % \
          (t.container.scoped_leaf, passed)

  for i in [("IDONE", True), (42, True), (-127, False), ("badstr", False)]:
    passed = True
    try:
      t.container.union_idref = i[0]
    except ValueError:
      passed = False

    assert passed is i[1], \
      "union with an identityref within it was not set " + \
        "correctly: %s != %s (%s)" % (passed, i[1], i[0])

  # check that typedefs nested in a container are supported
  passed = None
  try:
    t.scoped_container_typedef.two = "amber"
    passed = True
  except ValueError:
    passed = False

  assert passed is True, \
    "scoped typedef leaf within a container not set correctly"

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)


if __name__ == '__main__':
  main()
