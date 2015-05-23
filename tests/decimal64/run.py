#!/usr/bin/env python

import os, sys, getopt

TESTNAME="decimal"

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

  from bindings import decimal_ as d
  from decimal import Decimal

  q = d()

  for i in ["d1", "d2", "d3"]:
    assert hasattr(q.container, i), "container missing attribute - %s" % i

  q.container.d1 = 42.0
  assert len(str(q.container.d1).split(".")[1]) == 2, "precision for d1 was incorrect %s" % q.container.d1
  q.container.d2 = 42.0009
  assert q.container.d2 == Decimal("42.001"), "precision did not result in correct rounding (%s)" \
          % q.container.d2
  assert q.container.d2._default == Decimal("42.000"), "default was set wrong for d2 (%s)" \
          % q.container.d2._default
  assert q.container.d3._default == Decimal("1"), "default was set wrong for d3 (%s)" \
          % q.container.d3._default

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
