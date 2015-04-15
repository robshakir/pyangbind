#!/usr/bin/env python

import os, sys, getopt

TESTNAME="uint"

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

  this_dir = os.path.dirname(os.path.realpath(__file__))
  os.system("/Users/rjs/Code/pyang/bin/pyang --plugindir /Users/rjs/Code/pyangbind/btplugin -f bt -o %s/bindings.py %s/%s.yang" % (this_dir, this_dir, TESTNAME))

  from bindings import uint

  u = uint()

  for name in ["eight", "sixteen", "thirtytwo"]:
    for subname in ["", "default", "result", "restricted"]:
      assert hasattr(u.uint_container, "%s%s" % (name, subname)) == True, \
        "missing %s%s from container" % (name, subname)

  # tests default and equality
  for e in [("eight", 2**8-1), ("sixteen", 2**16-1), ("thirtytwo", 2**32-1)]:
    default_v = getattr(u.uint_container, "%sdefault" % e[0])._default
    assert default_v == e[1], \
      "defaults incorrectly set for %s, expected: %d, got %d" % (e[0], e[1], default_v)


  u.uint_container.eight = 42
  u.uint_container.sixteen = 42
  u.uint_container.thirtytwo = 42
  u.uint_container.eightdefault = 84
  u.uint_container.sixteendefault = 84
  u.uint_container.thirtytwodefault = 84
  for i in ["eight", "sixteen", "thirtytwo"]:
    v = getattr(u.uint_container, i)
    assert v == 42, "incorrectly set %s, expected 42, got %d" % (i, v)
    c = getattr(u.uint_container, "changed")()
    assert c == True, "incorrect changed flag for %s" % i

  # maybe we need to test math here

  e = False
  try:
    u.uint_container.eightrestricted = 11
  except:
    e = True
  assert e == True, "incorrectly allowed value outside of range for eightrestricted (11)"

  e = False
  try:
    u.uint_container.eightrestricted = 0
  except:
    e = True
  assert e == True, "incorrectly allowed value outside of range for eightrestricted (0)"

  e = False
  try:
    u.uint_container.sixteenrestricted = 1001
  except:
    e = True
  assert e == True, "incorrectly allowed value outside of range for sixteenrestricted (1001)"

  e = False
  try:
    u.uint_container.sixteenrestricted = 99
  except:
    e = True
  assert e == True, "incorrectly allowed value outside of range for sixteenrestricted (99)"

  e = False
  try:
    u.uint_container.thirtytworestricted = 500001
  except:
    e = True
  assert e == True, "incorrectly allowed value outside of range for thirtytworestricted (500001)"

  e = False
  try:
    u.uint_container.thirtytworestricted = 9999
  except:
    e = True
  assert e == True, "incorrectly allowed value outside of range for thirtytworestricted (9999)"

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
