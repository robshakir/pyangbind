#!/usr/bin/env python

import os, sys, getopt

TESTNAME="choice"

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

  pyangpath = os.environ.get('PYANGPATH') if os.environ.get('PYANGPATH') is not None else False
  pyangbindpath = os.environ.get('PYANGBINDPATH') if os.environ.get('PYANGBINDPATH') is not None else False
  assert not pyangpath == False, "could not find path to pyang"
  assert not pyangbindpath == False, "could not resolve pyangbind directory"

  this_dir = os.path.dirname(os.path.realpath(__file__))
  os.system("%s --plugindir %s -f pybind -o %s/bindings.py %s/%s.yang" % (pyangpath, pyangbindpath, this_dir, this_dir, TESTNAME))

  from bindings import choice
  t = choice()

  assert hasattr(t, "container"), "object does not have container"
  for i in ["case_one_container", "case_two_container"]:
    assert hasattr(t.container,i), "object does not have choice container, %s" % i
  for i in ["choice_one", "choice_two", "case_one", "case_two"]:
    assert not hasattr(t.container,i), "object has an erroneous choice option, %s" % i

  assert t.container.case_one_container.case_one_leaf == 0, "object does not have the correct value for case_one_leaf, %s" % t.container.case_one_container.case_one_leaf
  assert t.container.case_two_container.case_two_leaf == 0, "object does not have the correct value for case_two_leaf, %s" % t.container.case_two_container.case_two_leaf

  t.container.case_one_container.case_one_leaf = 42
  assert t.container.case_one_container.case_one_leaf == 42, "object did not specify a value within the choice correctly, %s" % t.container.case_one_container.case_one_leaf
  assert t.container.case_two_container.case_two_leaf == 0, "object erroneously set another value wtihin the choice, %s" % t.container.case_two_container.case_two_leaf

  t.container.case_two_container.case_two_leaf = 42
  assert t.container.case_two_container.case_two_leaf == 42, "object did not allow the other half of the choice to be specified, %s" % t.container.case_two_container.case_two_leaf
  assert t.container.case_one_container.case_one_leaf == 0, "object did not reset the value of the case-one side of the choice, %s" % t.container.case_one_container.case_one_leaf

  if not keepfiles:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
