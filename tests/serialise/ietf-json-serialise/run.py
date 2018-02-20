#!/usr/bin/env python

import os
import sys
import getopt
import json
import difflib
from pyangbind.lib.serialise import pybindJSONEncoder, pybindIETFJSONEncoder
from pyangbind.lib.pybindJSON import dumps
from decimal import Decimal

TESTNAME = "ietf-json-serialise"


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
  cmd += " %s/augment.yang" % this_dir
  os.system(cmd)

  from bindings import ietf_json_serialise
  from bitarray import bitarray
  from pyangbind.lib.xpathhelper import YANGPathHelper

  y = YANGPathHelper()
  js = ietf_json_serialise(path_helper=y)

  js.c1.l1.add(1)
  for s in ["int", "uint"]:
    for l in [8, 16, 32, 64]:
      name = "%s%s" % (s, l)
      x = getattr(js.c1.l1[1], "_set_%s" % name)
      x(1)
  js.c1.l1[1].restricted_integer = 6
  js.c1.l1[1].string = "bear"
  js.c1.l1[1].restricted_string = "aardvark"
  js.c1.l1[1].union = 16
  js.c1.l1[1].union_list.append(16)
  js.c1.l1[1].union_list.append("chicken")
  js.c1.l1[1].empty = True

  js.c1.t1.add(16)
  js.c1.t1.add(32)
  js.c1.l1[1].leafref = 16

  js.c1.l1[1].binary = bitarray("010101")
  js.c1.l1[1].boolean = True
  js.c1.l1[1].enumeration = "one"
  js.c1.l1[1].identityref = "idone"
  js.c1.l1[1].remote_identityref = "stilton"
  js.c1.l1[1].typedef_one = "test"
  js.c1.l1[1].typedef_two = 8
  js.c1.l1[1].one_leaf = "hi"
  js.c1.l1[1].uint64type = 2**22
  js.c1.l1[1].typedef_decimal = 32.29
  js.c1.l1[1].typedef_decimalrange = Decimal("33.44")
  js.c1.l1[1].range_decimal = Decimal("4.44443322")

  for i in range(1, 5):
    js.c1.l1[1].ll.append(unicode(i))
  js.c1.l1[1].next_hop.append("DROP")
  js.c1.l1[1].next_hop.append("192.0.2.1")
  js.c1.l1[1].next_hop.append("TEST")

  js.augtarget.augleaf = "teststring"

  js.c1.l1[1].decleaf = Decimal('42.4422')

  for i in range(1, 10):
    js.c1.l2.add(i)

  pybind_json = json.loads(json.dumps(
                  pybindIETFJSONEncoder.generate_element(js, flt=True),
                  cls=pybindIETFJSONEncoder, indent=4))
  external_json = json.load(
                      open(os.path.join(this_dir, "json", "obj.json"), 'r'))

  assert pybind_json == external_json, "JSON did not match the expected output, " + \
	"diff: %s\n" % diff(pybind_json, external_json)

  # Check that we can serialise a single element on its own.
  pybind_json = json.loads(json.dumps(
                  pybindIETFJSONEncoder.generate_element(js.c1.l1[1].string, flt=True),
                  cls=pybindIETFJSONEncoder, indent=4))
  assert pybind_json == "bear", "Single element JSON did not match the expected output"

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

def diff(a, b):
    ja = json.dumps(a, indent=4, sort_keys=True).split("\n")
    jb = json.dumps(b, indent=4, sort_keys=True).split("\n")
    return '\n'.join(difflib.unified_diff(ja, jb))

if __name__ == '__main__':
  main()
