#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "nested"


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

  from bindings import nested

  test_instance = nested()

  assert test_instance.container.subcontainer._changed() is False, \
    "subcontainer was marked to changed"

  assert test_instance.container._changed() is False, \
    "container was marked to changed"

  test_instance.container.subcontainer.a_leaf = 1

  assert test_instance.container.subcontainer._changed() is True, \
    "subcontainer not marked to changed after change"

  assert test_instance.container.subcontainer.get() == {'a-leaf': 1}, \
    "subcontainer get not correct"

  assert test_instance.container.get() == {'subcontainer': {'a-leaf': 1}}, \
    "container get not correct"

  assert test_instance.get() == \
    {'container': {'subcontainer': {'a-leaf': 1}}}, \
      "instance get not correct"

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)


if __name__ == '__main__':
  main()
