#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "identityref"


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

  from bindings import identityref

  i = identityref()

  for j in ["id1", "idr1"]:
    assert hasattr(i.test_container, j), \
        "%s leaf does not exist in the container" % i

  assert i.test_container.id1 == "", \
      "id1 leaf had an unexpected value (%s)" % i.test_container.id1
  assert i.test_container.idr1 == "", \
      "idr1 leaf had an unexpected value (%s)" % i.test_container.idr1

  passed = True
  try:
    i.test_container.id1 = "hello"
  except ValueError:
    passed = False
  assert passed is False, "id1 leaf set to invalid value"

  for k in ["option-one", "option-two"]:
    passed = True
    i.test_container.id1 = k
    try:
      i.test_container.id1 = k
    except ValueError:
      passed = False
    assert passed is True, \
        "id1 leaf was set to an invalid value (%s, %s)" % (passed, k)

  # checks that the namespaces are right
  for k in ["remote-one", "remote-two"]:
    passed = True
    try:
      i.test_container.idr1 = k
    except ValueError:
      passed = False
    assert passed is True, "idr1 leaf was set to an invalid value (%s)" % k

  if not keepfiles:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
