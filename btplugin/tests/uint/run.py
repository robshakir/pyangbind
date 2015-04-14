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
  os.system("/Users/rjs/Code/pyangbind/bin/pyang --plugindir /Users/rjs/Code/pyangbind/btplugin -f bt -o %s/bindings.py %s/%s.yang" % (this_dir, this_dir, TESTNAME))

  from bindings import uint

  u = uint()

  for name in ["eight", "sixteen", "thirtytwo"]:
    for subname in ["", "default", "result"]:
      assert hasattr(u.uint_container, "%s%s" % (name, subname)) == True, \
        "missing %s%s from container" % (name, subname)

  for e in [("eight", 2**8-1), ("sixteen", 2**16-1), ("thirtytwo", 2**32-1)]:
    default_v = getattr(u.uint_container, "%sdefault" % e[0])._default
    assert default_v == e[1], \
      "defaults incorrectly set for %s, expected: %d, got %d" % (e[0], e[1], default_v)

  # default, equality, changed
  # addition, subtraction, multiplication, division for each type

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
