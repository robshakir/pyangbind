#!/usr/bin/env python

import os, sys, getopt

TESTNAME="nested"

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

  from bindings import nested

  test_instance = nested()

  assert test_instance.container.subcontainer._changed() == False, \
    "subcontainer was marked to changed"

  assert test_instance.container._changed() == False, \
    "container was marked to changed"

  test_instance.container.subcontainer.a_leaf = 1

  assert test_instance.container.subcontainer._changed() == True, \
    "subcontainer not marked to changed after change"

  assert test_instance.container.subcontainer.get() == {'a-leaf': 1}, \
    "subcontainer get not correct"

  assert test_instance.container.get() == {'subcontainer': {'a-leaf': 1}}, \
    "container get not correct"

  assert test_instance.get() == {'container': {'subcontainer': {'a-leaf': 1}}}, \
    "instance get not correct"

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
