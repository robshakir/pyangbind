#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "choice"


# generate bindings in this folder
def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError as e:
    print(str(e))
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

  from bindings import choice
  t = choice()

  assert hasattr(t, "container"), "object does not have container"
  for i in ["case_one_container", "case_two_container"]:
    assert hasattr(t.container, i), "object does not have choice container" + \
        ", %s" % i
  for i in ["choice_one", "choice_two", "case_one", "case_two"]:
    assert not hasattr(t.container, i), \
        "object has an erroneous choice option, %s" % i

  assert t.container.case_one_container.case_one_leaf == 0, \
      "object does not have the correct value for case_one_leaf, %s" % \
          t.container.case_one_container.case_one_leaf
  assert t.container.case_two_container.case_two_leaf == 0, \
      "object does not have the correct value for case_two_leaf, %s" % \
          t.container.case_two_container.case_two_leaf

  t.container.case_one_container.case_one_leaf = 42
  assert t.container.case_one_container.case_one_leaf == 42, \
      "object did not specify a value within the choice correctly, %s" \
          % t.container.case_one_container.case_one_leaf
  assert t.container.case_two_container.case_two_leaf == 0, \
      "object erroneously set another value wtihin the choice, %s" \
        % t.container.case_two_container.case_two_leaf

  t.container.case_two_container.case_two_leaf = 42
  assert t.container.case_two_container.case_two_leaf == 42, \
      "object did not allow the other half of the choice to be specified, %s" \
        % t.container.case_two_container.case_two_leaf
  assert t.container.case_one_container.case_one_leaf == 0, \
    "object did not reset the value of the case-one side of the choice, %s" \
       % t.container.case_one_container.case_one_leaf


  t.container.case_one_container.user.add("first")
  assert t.container.case_one_container.user["first"].username == "first", \
       "object has the wrong username for user in case one list"

  t.container.case_two_container.user.add("second")
  assert t.container.case_two_container.user["second"].username == "second", \
       "object has the wrong username for user in case two list"
  assert len(t.container.case_one_container.user.keys()) == 0, \
       "Adding to the second user list did not remove entries from the first"

  if not keepfiles:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
