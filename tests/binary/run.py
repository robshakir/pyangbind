#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "binary"


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

  from bindings import binary as b
  from bitarray import bitarray
  t = b()

  for i in ["b1", "b2", "b3"]:
    assert hasattr(t.container, i), \
        "element did not exist in container (%s)" % i

  for value in [
      ("01110", True, [False, True, True, True, False],),
          ({"42": 42}, True, [True])]:
    passed = True
    try:
      t.container.b1 = value[0]
    except Exception:
      passed = False
    assert passed == value[1], "could incorrectly set b1 to %s" % value[0]

  assert t.container.b2._default == bitarray("0100"), \
    "Default for leaf b2 was not set correctly (%s != %s)" \
       % (t.container.b2._default, bitarray("0100"))

  assert t.container.b2 == bitarray(), \
    "Value of bitarray was not null when checking b2 (%s != %s)" \
        % (t.container.b2, bitarray())

  assert t.container.b2._changed() is False, \
    "Unset bitarray specified changed when was default (%s != False)" \
        % (t.container.b2._changed())

  t.container.b2 = bitarray("010")
  assert t.container.b2 == bitarray('010'), \
    "Bitarray not successfuly set (%s != %s)" % \
        (t.container.b2, bitarray('010'))

  assert t.container.b2._changed() is True, \
    "Bitarray value not flagged as changed (%s != %s)" % \
        (t.container.b2._changed(), True)

  for v in [("0", False), ("1000000011110000", True),
              ("111111110000000011111111", False)]:
    try:
      t.container.b3 = v[0]
      passed = True
    except ValueError:
      passed = False
    assert passed == v[1], \
        "limited length binary incorrectly set to %s (%s != %s)" \
          % (v[0], v[1], passed)

  for v in [("0", False), ("1111111100000000", True),
            ("111111110000000011111111", True),
            ("1111111100000000111111110000000011110000", False)]:
    try:
      t.container.b4 = v[0]
      passed = True
    except ValueError:
      passed = False
    assert passed == v[1], "limited length binary with range incorrectly " + \
      "set to %s (%s != %s)" % (v[0], v[1], passed)

  for v in [("0", False), ("1111000011110000", True),
            ("111100001111000011110000", True),
            ("1111000011110000111100001111000011110000", False),
            ("111100001111000011110000111100001111000011110000", True),
            ("111100001111000011110000111100001111000011110000" +
              "11110000111100001111000011110000", True),
            ("111100001111000011110000111100001111000011110000" +
              "111100001111000011110000111100001111000011110000" +
              "111100001111000011110000111100001111000011110000" +
              "111100001111000011110000111100001111000011110000" +
              "111100001111000011110000111100001111000011110000" +
              "111100001111000011110000111100001111000011110000" +
              "111100001111000011110000111100001111000011110000" +
              "1010101010101010", False)]:
    try:
      t.container.b5 = v[0]
      passed = True
    except Exception:
      passed = False
    assert passed == v[1], "limited length binary with complex length " + \
        "argument incorrectly set to %s (%s != %s)" % (v[0], v[1], passed)

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)


if __name__ == '__main__':
  main()
