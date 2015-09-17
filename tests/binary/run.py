#!/usr/bin/env python

import os, sys, getopt

TESTNAME="binary"

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

  from bindings import binary as b
  from bitarray import bitarray
  t = b()

  for i in ["b1", "b2", "b3"]:
    assert hasattr(t.container, i), "element did not exist in container (%s)" \
      % i

  for value in [("01110", True, [False, True, True, True, False],), \
                ({"42": 42}, True, [True]), \
               ]:
    passed = True
    try:
      t.container.b1 = value[0]
    except:
      passed = False
    assert passed == value[1], "could incorrectly set b1 to %s" % value[0]

  assert t.container.b2._default == bitarray("0100"), \
    "Default for leaf b2 was not set correctly (%s != %s)" \
       % (t.container.b2._default, bitarray("0100"))
  assert t.container.b2 == bitarray(), \
    "Value of bitarray was not null when checking b2 (%s != %s)" \
        % (t.container.b2, bitarray())
  assert t.container.b2._changed() == False, \
    "Unset bitarray specified changed when was default (%s != False)" \
        % (t.container.b2._changed())
  t.container.b2 = bitarray("010")
  assert t.container.b2 == bitarray('010'), \
    "Bitarray not successfuly set (%s != %s)" % (t.container.b2, bitarray('010'))
  assert t.container.b2._changed() == True, \
    "Bitarray value not flagged as changed (%s != %s)" % (t.container.b2._changed(), True)

  for v in [("0", True), ("01", True), ("010", False)]:
    try:
      t.container.b3 = v[0]
      passed = True
    except ValueError:
      passed = False
    assert passed == v[1], "limited length binary incorrectly set to %s (%s != %s)" \
      % (v[0], v[1], passed)

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
