#!/usr/bin/env python

import os, sys, getopt

TESTNAME="int"

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

  from bindings import int_ as i

  u = i()

  for name in ["eight", "sixteen", "thirtytwo", "sixtyfour"]:
    for subname in ["", "default", "result", "restricted"]:
      assert hasattr(u.int_container, "%s%s" % (name, subname)) == True, \
        "missing %s%s from container" % (name, subname)

  # tests default and equality
  for e in [("eight", 2**7-1), ("sixteen", 2**15-1), ("thirtytwo", 2**31-1), ("sixtyfour", 2**63-1)]:
    default_v = getattr(u.int_container, "%sdefault" % e[0])._default
    assert default_v == e[1], \
      "defaults incorrectly set for %s, expected: %d, got %d" % (e[0], e[1], default_v)


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
    assert c == True, "incorrect changed flag for %s" % i

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
    assert passed == True, "could not set value of %srestricted to 10" % i

  e = False
  try:
    u.int_container.eightrestricted = -100
  except ValueError:
    e = True
  assert e == True, "incorrectly allowed value outside of range for eightrestricted (-100)"

  e = False
  try:
    u.int_container.eightrestricted = 1001
  except ValueError:
    e = True
  assert e == True, "incorrectly allowed value outside of range for eightrestricted (1001)"

  e = False
  try:
    u.int_container.sixteenrestricted = -43
  except ValueError:
    e = True
  assert e == True, "incorrectly allowed value outside of range for sixteenrestricted (-43)"

  e = False
  try:
    u.int_container.sixteenrestricted = 1001
  except ValueError:
    e = True
  assert e == True, "incorrectly allowed value outside of range for sixteenrestricted (1001)"

  e = False
  try:
    u.int_container.thirtytworestricted = 500001
  except ValueError:
    e = True
  assert e == True, "incorrectly allowed value outside of range for thirtytworestricted (500001)"

  e = False
  try:
    u.int_container.thirtytworestricted = -43
  except ValueError:
    e = True
  assert e == True, "incorrectly allowed value outside of range for thirtytworestricted (9999)"

  e = False
  try:
    u.int_container.sixtyfourrestricted = 72036854775809
  except ValueError:
    e = True
  assert e == True, "incorrectly allowed value outside of range for sixtyfourrestricted (72036854775809)"

  e = False
  try:
    u.int_container.sixtyfourrestricted = -43
  except ValueError:
    e = True
  assert e == True, "incorrectly allowed value outside of range for sixtyfourrestricted (-43)"

  for i in [(0,True), (10,True),(-10,False)]:
    passed = False
    try:
      u.int_container.restricted_ueight_max = i[0]
      passed = True
    except ValueError:
      pass
    assert passed == i[1], "restricted range using max was not set correctly (%d -> %s != %s)" % \
      (i[0], passed, i[1])

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
