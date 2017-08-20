#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "int"


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

  from bindings import int_ as bindings_int

  u = bindings_int()

  for name in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
    for subname in ["", "default", "result", "restricted"]:
      assert hasattr(u.int_container, "%s%s" % (name, subname)) is True, \
          "missing %s%s from container" % (name, subname)

  # tests default and equality
  for e in [("eight", 2**7 - 1), ("sixteen", 2**15 - 1),
            ("thirtytwo", 2**31 - 1), ("sixtyfour", 2**63 - 1)]:
    default_v = getattr(u.int_container, "%sdefault" % e[0])._default
    assert default_v == e[1], \
      "defaults incorrectly set for %s, expected: %d, got %d" \
          % (e[0], e[1], default_v)

  u.int_container.eight = 42
  u.int_container.sixteen = 42
  u.int_container.thirtytwo = 42
  u.int_container.sixtyfour = 42
  u.int_container.eightdefault = 84
  u.int_container.sixteendefault = 84
  u.int_container.thirtytwodefault = 84
  u.int_container.sixtyfourdefault = 84
  for i in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
    v = getattr(u.int_container, i)
    assert v == 42, "incorrectly set %s, expected 42, got %d" % (i, v)
    c = getattr(u.int_container, "_changed")()
    assert c is True, "incorrect changed flag for %s" % i

  # test math + negatives
  u.int_container.eight = 42
  u.int_container.sixteen = 42
  u.int_container.thirtytwo = 42
  u.int_container.sixtyfour = 42
  u.int_container.eight *= -1
  u.int_container.sixteen *= -1
  u.int_container.thirtytwo *= -1
  u.int_container.sixtyfour *= -1
  for i in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
    v = getattr(u.int_container, i)
    assert v == -42, "incorrectly set %s, expected 42, got %d" % (i, v)

  for i in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
    passed = False
    try:
      setattr(u.int_container, "%srestricted" % i, 10)
      passed = True
    except ValueError:
      pass
    assert passed is True, "could not set value of %srestricted to 10" % i

  e = False
  try:
    u.int_container.eightrestricted = -100
  except ValueError:
    e = True
  assert e is True, \
      "incorrectly allowed value outside of range for eightrestricted (-100)"

  e = False
  try:
    u.int_container.eightrestricted = 1001
  except ValueError:
    e = True
  assert e is True, \
      "incorrectly allowed value outside of range for eightrestricted (1001)"

  e = False
  try:
    u.int_container.sixteenrestricted = -43
  except ValueError:
    e = True
  assert e is True, \
    \
      "incorrectly allowed value outside of range for sixteenrestricted (-43)"

  e = False
  try:
    u.int_container.sixteenrestricted = 1001
  except ValueError:
    e = True
  assert e is True, \
    "incorrectly allowed value outside of range for sixteenrestricted (1001)"

  e = False
  try:
    u.int_container.thirtytworestricted = 500001
  except ValueError:
    e = True
  assert e is True, \
    "incorrectly allowed value outside of range for thirtytworestricted " + \
        "(500001)"

  e = False
  try:
    u.int_container.thirtytworestricted = -43
  except ValueError:
    e = True
  assert e is True, \
    "incorrectly allowed value outside of range for thirtytworestricted (9999)"

  e = False
  try:
    u.int_container.sixtyfourrestricted = 72036854775809
  except ValueError:
    e = True
  assert e is True, \
    "incorrectly allowed value outside of range for sixtyfourrestricted " + \
        "(72036854775809)"

  e = False
  try:
    u.int_container.sixtyfourrestricted = -43
  except ValueError:
    e = True
  assert e is True, \
    "incorrectly allowed value outside of range for sixtyfourrestricted (-43)"

  for i in [(0, True), (10, True), (-10, False)]:
    passed = False
    try:
      u.int_container.restricted_ueight_max = i[0]
      passed = True
    except ValueError:
      pass
    assert passed == i[1], \
        "restricted range using max was not set correctly (%d -> %s != %s)" % \
            (i[0], passed, i[1])

  for i in [(0, True), (10, True), (-128, True), (-300, False)]:
    passed = False
    try:
      u.int_container.restricted_ueight_min = i[0]
      passed = True
    except ValueError:
      pass
    assert passed == i[1], \
        "restricted range using min was not set correctly (%d -> %s != %s)" % \
            (i[0], passed, i[1])

  for i in [(0, True), (10, True), (-128, True), (-300, False)]:
    passed = False
    try:
      u.int_container.restricted_ueight_min_alias = i[0]
      passed = True
    except ValueError:
      pass
    assert passed == i[1], \
        "restricted range using min alias was not set correctly (%d -> %s != %s)" % \
            (i[0], passed, i[1])

  for i in [(0, True), (13, False), (-20, False), (5, True), (16, True)]:
    passed = False
    try:
      u.int_container.complex_range = i[0]
      passed = True
    except ValueError:
      pass
    assert passed == i[1], \
        "complex range was not set correctly (%d -> %s != %s)" % \
            (i[0], passed, i[1])

    passed = False
    try:
      u.int_container.complex_range_two = i[0]
      passed = True
    except ValueError:
      pass
    assert passed == i[1], \
        "complex range with spaces and three elements not set correctly " + \
            "(%d -> %s != %s)" % (i[0], passed, i[1])

  for i in [(-2, True), (42, False)]:
    passed = False
    try:
      u.int_container.complex_range_with_negative = i[0]
      passed = True
    except ValueError:
      pass
    assert passed == i[1], \
         "complex range with negatives not set correctly (%d -> %s != %s)" % \
              (i[0], passed, i[1])

  for i in [(-11, False), (-5, True), (0, False), (5, False), (10, True),
            (25, True), (31, False)]:
    passed = False
    try:
      u.int_container.intLeafWithRange = i[0]
      passed = True
    except ValueError:
      pass
    assert passed == i[1], \
        "complex range with negatives and additional spaces not set " + \
            "correctly (%d -> %s != %s)" % (i[0], passed, i[1])

  for i in [(-43, False), (-40, True), (98, False), (122, True), (254, False),
            (255, True), (256, False)]:
    passed = False
    try:
      u.int_container.complex_range_with_equals_case = i[0]
      passed = True
    except ValueError:
      pass
    assert passed == i[1], \
        "complex range with equals case was not set correctly " + \
            " (%d -> %s != %s)" % (i[0], passed, i[1])
  bounds = {
    'eight': (-2**7, 2**7 - 1),
    'sixteen': (-2**15, 2**15 - 1),
    'thirtytwo': (-2**31, 2**31 - 1),
    'sixtyfour': (-2**63, 2**63 - 1),
  }

  for elem, vals in bounds.items():
    set_attr = getattr(u.int_container, "_set_%s" % elem, None)
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

  try:
    u.int_container.restricted_ueight_min_alias = -2**7
  except ValueError:
    assert False, "Could not set min..max int8 to the minimum value"

  try:
    u.int_container.restricted_ueight_min_alias = 2**7 - 1
  except ValueError:
    assert False, "Could not set min..max int8 to the maximum value"

  try:
    u.int_container.restricted_ueight_min_alias = -2**7 - 1
  except ValueError:
    pass
  else:
    assert False, "Incorrectly set min..max int8 to the min value minus one"

  try:
    u.int_container.restricted_ueight_min_alias = 2**7 + 1
  except ValueError:
    pass
  else:
    assert False, "Incorrectly set min..max int8 to the max value plus one"

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)


if __name__ == '__main__':
  main()
