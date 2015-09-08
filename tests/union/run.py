#!/usr/bin/env python

import os, sys, getopt

TESTNAME="union"

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

  from bindings import union
  import numpy

  u = union()

  for i in ["u1", "u2", "u3", "u4", "u6", "u7", "u8"]:
    assert hasattr(u.container, i), "container was missing attribute %s" % i

  # need to test some oddities of ordering in unions

  # u1: precedence of int over string
  u.container.u1 = 2
  u.container.u1 += 1
  assert u.container.u1 == 3, \
  "union with int over string precedence did not result in element acting as int (%s)" % \
    u.container.u1
  u.container.u1 = "aStringTest"
  assert u.container.u1 == "aStringTest", \
  "union of int and string could not be set to a string correctly"
  u.container.u1 += "A"
  assert u.container.u1 == "aStringTestA", \
  "union of int and string when set to string had wrong addition (%s)" \
    % u.container.u1

  # u2: precedence of string over int, with a default set
  assert len(u.container.u2) == 0, \
  "union with a default set was equal to it, rather than a zero length string (%s)" \
    % len(u.container.u2)
  assert u.container.u2._default == "set from u2", \
    "union with a default did not have the correct value (%s)" \
      % u.container.u2._default
  u.container.u2 = 2
  u.container.u2 += "A"
  assert u.container.u2 == "2A", \
    "union with precedence {str,int} did not add correctly (%s)" \
      % u.container.u2

  # u3: union of int with precendence over string, but default is a string
  assert u.container.u3 == 0, \
    "union with a default set directly was equal to it rather than an int of value 0 (%s)" \
      % u.container.u3
  assert u.container.u3._default == "set from u3", \
    "union with a default that skipped a type did not have the correct value (%s)" \
      % u.container.u3._default

  assert type(u.container.u4._default) == numpy.int8, \
    "union with integer default did not have integer type default (%s)" % \
      type(u.container.u4._default)

  assert type(u.container.u6._default) == unicode, \
    "union with an inherited default from a typedef did not do so correctly (%s)" % \
      type(u.container.u6._default)

  u.container.u7 = "hello"
  assert u.container.u7 == "hello", \
    "leaf with union specified within a typedef not correctly set to string (%s)" % \
      u.container.u7
  u.container.u7 = 10
  assert u.container.u7 == 10, \
    "leaf with union specified within a typdef not correctly set to int (%s)" % \
      u.container.u7

  assert u.container.u8._default == 10, \
    "leaf with default int specified within a union (that was in a typedef) was not set correctly (%s)" % \
      u.container.u8._default

  from bitarray import bitarray
  for i in [(1, True), ("hello", True), (42.42, True), (True, True), (bitarray(10), False)]:
    passed = False
    try:
      u.container.u9.append(i[0])
      passed = True
    except ValueError:
      pass
    assert passed == i[1], \
      "leaf-list of union of unions did not correctly validate value " + \
        "(%s -> %s != %s)" % (i[0], passed, i[1])

  # 10-20, 30-40 or starting with a and b
  for i in [(15,True), (35,True), ("aardvark", True), ("bear", True),
            (21, False), (42, False), ("cat", False), ("fish", False)]:
    passed = False
    try:
      u.container.u10.append(i[0])
      passed = True
    except ValueError:
      pass
    assert passed == i[1], \
      "leaf-list of union of unions that had restricted types did not " \
      + "correctly validate the value (%s -> %s != %s)" % (i[0], passed, i[1])

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
