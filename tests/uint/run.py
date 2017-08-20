#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "uint"


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

  from bindings import uint

  u = uint()

  for name in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
    for subname in ["", "default", "result", "restricted"]:
      assert hasattr(u.uint_container, "%s%s" % (name, subname)) is True, \
          "missing %s%s from container" % (name, subname)

  # tests default and equality
  for e in [("eight", 2**8 - 1), ("sixteen", 2**16 - 1),
            ("thirtytwo", 2**32 - 1), ("sixtyfour", 2**64 - 1)]:
    default_v = getattr(u.uint_container, "%sdefault" % e[0])._default
    assert default_v == e[1], \
      "defaults incorrectly set for %s, expected: %d, got %d" \
          % (e[0], e[1], default_v)

  u.uint_container.eight = 42
  u.uint_container.sixteen = 42
  u.uint_container.thirtytwo = 42
  u.uint_container.sixtyfour = 42
  u.uint_container.eightdefault = 84
  u.uint_container.sixteendefault = 84
  u.uint_container.thirtytwodefault = 84
  u.uint_container.sixtyfourdefault = 84
  for i in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
    v = getattr(u.uint_container, i)
    assert v == 42, "incorrectly set %s, expected 42, got %d" % (i, v)
    c = getattr(u.uint_container, "_changed")()
    assert c is True, "incorrect changed flag for %s" % i

  # maybe we need to test math here

  e = False
  try:
    u.uint_container.eightrestricted = 11
  except ValueError:
    e = True
  assert e is True, \
     "incorrectly allowed value outside of range for eightrestricted (11)"

  e = False
  try:
    u.uint_container.eightrestricted = 0
  except ValueError:
    e = True
  assert e is True, \
     "incorrectly allowed value outside of range for eightrestricted (0)"

  e = False
  try:
    u.uint_container.sixteenrestricted = 1001
  except ValueError:
    e = True
  assert e is True, \
     "incorrectly allowed value outside of range for sixteenrestricted (1001)"

  e = False
  try:
    u.uint_container.sixteenrestricted = 99
  except ValueError:
    e = True
  assert e is True, \
     "incorrectly allowed value outside of range for sixteenrestricted (99)"

  e = False
  try:
    u.uint_container.thirtytworestricted = 500001
  except ValueError:
    e = True
  assert e is True, \
     "incorrectly allowed value outside of range for thirtytworestricted " + \
        "(500001)"

  e = False
  try:
    u.uint_container.thirtytworestricted = 9999
  except ValueError:
    e = True
  assert e is True, \
     "incorrectly allowed value outside of range for thirtytworestricted " + \
          "(9999)"

  e = False
  try:
    u.uint_container.sixtyfourrestricted = 18446744073709551615
  except ValueError:
    e = True
  assert e is True, \
     "incorrectly allowed value outside of range for sixtyfourrestricted " + \
        "(18446744073709551615)"

  e = False
  try:
    u.uint_container.sixtyfourrestricted = 799
  except ValueError:
    e = True
  assert e is True, \
     "incorrectly allowed value outside of range for sixtyfourrestricted (799)"

  for v in [(0, True), (10, True), (2**32 - 1, True), (2**64, False),
              (2**32, False)]:
    val_set = False
    try:
      u.issue_fixes.region_id = v[0]
      val_set = True
    except ValueError:
      pass
    assert v[1] is val_set, "Value of region_id incorrectly set %s (%s != %s" \
      % (v[0], val_set, v[1])

  bounds = {
    'eight': (0, 2**8 - 1),
    'sixteen': (0, 2**16 - 1),
    'thirtytwo': (0, 2**32 - 1),
    'sixtyfour': (0, 2**64 - 1),
  }

  for elem, vals in bounds.items():
    set_attr = getattr(u.uint_container, "_set_%s" % elem, None)
    assert set_attr is not None, "Could not find attribute"
    for val in vals:
      passed = True
      try:
        set_attr(vals[0])
      except ValueError:
        passed = False
      assert passed is True, "Could not set int size %s to %d" % \
        (elem, val)

    passed = False
    try:
      set_attr(vals[0] - 1)
    except ValueError:
      passed = True

    assert passed is True, "Incorrectly set int size %s to %d" % \
      (elem, vals[0] - 1)

    passed = False
    try:
      set_attr(vals[1] + 1)
    except ValueError:
      passed = True

    assert passed is True, "Incorrectly set int size %s to %d" % \
      (elem, vals[1] + 1)

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)


if __name__ == '__main__':
  main()
