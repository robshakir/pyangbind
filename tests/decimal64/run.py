#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "decimal"


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

  import bindings
  from bindings import decimal_ as d
  from decimal import Decimal

  q = d()

  for i in ["d1", "d2", "d3"]:
    assert hasattr(q.container, i), "container missing attribute - %s" % i

  q.container.d1 = 42.0
  assert len(str(q.container.d1).split(".")[1]) == 2, \
      "precision for d1 was incorrect %s" % q.container.d1
  q.container.d2 = 42.0009
  assert q.container.d2 == Decimal("42.001"), \
      "precision did not result in correct rounding (%s)" \
          % q.container.d2
  assert q.container.d2._default == Decimal("42.000"), \
      "default was set wrong for d2 (%s)" \
          % q.container.d2._default
  assert q.container.d3._default == Decimal("1"), \
      "default was set wrong for d3 (%s)" \
          % q.container.d3._default

  for i in [(-452.6729, False), (-444.44, True), (-443.22, False),
            (-330, True), (-222.21, False), (111.2, False), (111.1, True),
            (446.56, True), (555.55559282, False)]:
    passed = False
    try:
      q.container.dec64LeafWithRange = i[0]
      passed = True
    except ValueError:
      pass
    assert passed == i[1], \
        "decimal64 leaf with range was not correctly set (%f -> %s != %s)" \
            % (i[0], passed, i[1])

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
