#!/usr/bin/env python

import os
import sys
import getopt
import json
from jsondiff import diff
from pyangbind.lib.serialise import pybindJSONDecoder
from pyangbind.lib.pybindJSON import dumps
from bitarray import bitarray
from collections import OrderedDict
from decimal import Decimal

TESTNAME = "ietf-json-deserialise"


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
  os.system(cmd)

  import bindings
  from bindings import ietf_json_deserialise

  pth = os.path.join(this_dir, "json", "mkeylist.json")
  nobj = pybindJSONDecoder.load_ietf_json(json.load(open(pth, 'r')),
            bindings, "ietf_json_deserialise")
  expected_get = {'mkey': {u'one 1': {'leaf-two': 1, 'leaf-one': u'one'},
                  u'three 2': {'leaf-two': 2, 'leaf-one': u'three'}}}
  assert nobj.get(filter=True) == expected_get, \
          "Multikey list load did not return expected JSON"
  del nobj

  pth = os.path.join(this_dir, "json", "skeylist.json")
  nobj = pybindJSONDecoder.load_ietf_json(json.load(open(pth, 'r')),
            bindings, "ietf_json_deserialise")
  expected_get = {'skey': {u'one': {'leaf-one': u'one'}, u'three':
                  {'leaf-one': u'three'}, u'two': {'leaf-one': u'two'}}}
  assert nobj.get(filter=True) == expected_get, "Single key list load did " + \
            "not return expected JSON"
  del nobj

  pth = os.path.join(this_dir, "json", "chlist.json")
  nobj = pybindJSONDecoder.load_ietf_json(json.load(open(pth, 'r')),
              bindings, "ietf_json_deserialise")
  expected_get = {'chlist': {1: {'keyleaf': 1, 'child': {'number': 1,
                    'string': u'one'}}, 2: {'keyleaf': 2,
                      'child': {'number': 2, 'string': u'two'}}}}
  assert nobj.get(filter=True) == expected_get, "List with children load " + \
              "did not return expected JSON"

  pth = os.path.join(this_dir, "json", "complete-obj.json")
  nobj = pybindJSONDecoder.load_ietf_json(json.load(open(pth, 'r')),
                bindings, "ietf_json_deserialise")
  expected_get = {
    "c1": {
      "l1": {
        1:
          {
            "one-leaf": "hi",
            "typedef-one": "test",
            "boolean": True,
            "binary": bitarray("111111"),
            "union": "16",
            "identityref": "idone",
            "enumeration": "one",
            "k1": 1,
            "uint16": 1,
            "union-list": [16, "chicken"],
            "uint32": 1,
            "empty": True,
            "int32": 1,
            "int16": 1,
            "string": "bear",
            "typedef-two": 8,
            "uint8": 1,
            "restricted-integer": 6,
            "leafref": "16",
            "int8": 1,
            "uint64": 1,
            "remote-identityref": "remote:stilton",
            "int64": 1,
            "restricted-string": "aardvark",
            "decimal": Decimal('16.32')
          }
      },
      "l2": OrderedDict(
              [
                (1, {"k1": 1}),
                (2, {"k1": 2}),
                (3, {"k1": 3}),
                (4, {"k1": 4}),
                (5, {"k1": 5}),
                (6, {"k1": 6}),
                (7, {"k1": 7}),
                (8, {"k1": 8}),
                (9, {"k1": 9})
              ]),
      "t1": {
          "32": {"target": "32"},
          "16": {"target": "16"}
      }
    }
  }
  actual_get = nobj.get(filter=True)
  assert actual_get == expected_get, "Deserialisation of " + \
    "complete object not as expected. Actual: %s\nExpected: %s\n\nDiff:%s" % (actual_get, expected_get, diff(actual_get, expected_get))

  pth = os.path.join(this_dir, "json", "nonexistkey.json")
  for i in [True, False]:
    nobj = None
    success = True
    try:
      nobj = pybindJSONDecoder.load_ietf_json(json.load(open(pth, 'r')),
        bindings, "ietf_json_deserialise", skip_unknown=i)
    except AttributeError:
      success = False

    assert success is i, "Skipping keys that did not exist was not" + \
      " successfully handled"


  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
