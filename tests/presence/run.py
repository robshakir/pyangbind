#!/usr/bin/env python

import os
import sys
import getopt
import unittest
import importlib
from pyangbind.lib.yangtypes import safe_name
import pyangbind.lib.pybindJSON as pbJ
import json

TESTNAME = "presence"

k = False

# generate bindings in this folder
def setup_test():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError as e:
    sys.exit(127)

  global k
  global this_dir

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
  cmd += " --use-extmethods"
  cmd += " --presence"
  cmd += " %s/%s.yang" % (this_dir, TESTNAME)
  os.system(cmd)

def teardown_test():
  global k
  global this_dir

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

class PyangbindPresenceTests(unittest.TestCase):

  def __init__(self, *args, **kwargs):
    unittest.TestCase.__init__(self, *args, **kwargs)

    err = None
    try:
      globals()["bindings"] = importlib.import_module("bindings")
    except ImportError as e:
      err = e
    self.assertIs(err, None)
    self.instance = bindings.presence()

  def test_001_check_containers(self):
    for attr in ["empty-container", "parent", ["parent", "child"]]:
      if isinstance(attr, list):
        parent = self.instance
        for v in attr:
          parent = getattr(parent, v, None)
          self.assertIsNot(parent, None)
      else:
        elem = getattr(self.instance, safe_name(attr), None)
        self.assertIsNot(elem, None)

  def test_002_check_presence(self):
    self.assertIs(self.instance.empty_container._presence, True)
    self.assertIs(self.instance.empty_container._cpresent, False)
    self.assertIs(self.instance.empty_container._present(), False)

  def test_003_check_set_present(self):
    smt = getattr(self.instance.empty_container, "_set_present", None)
    self.assertIsNot(smt, None)
    smt()
    self.assertIs(self.instance.empty_container._cpresent, True)
    self.assertIs(self.instance.empty_container._present(), True)

  def test_004_check_np(self):
    self.assertIs(self.instance.parent._presence, False)
    self.assertIs(self.instance.np_container._presence, False)
    self.assertIs(self.instance.np_container.s._presence, None)

  def test_005_check_hierarchy(self):
    self.assertIs(self.instance.pp._presence, True)
    self.assertIs(self.instance.pp._present(), False)
    self.assertIs(self.instance.pp._changed(), False)
    self.instance.pp.s = "teststring"
    self.assertIs(self.instance.pp._present(), True)
    self.assertIs(self.instance.pp._changed(), True)

  def test_006_check_invalid_hierarchy(self):
    self.assertIs(self.instance.parent._presence, False)
    self.assertIs(self.instance.parent.child._presence, True)
    self.assertIs(self.instance.parent.child._present(), False)
    self.instance.parent.child._set_present()
    self.assertIs(self.instance.parent.child._present(), True)
    self.assertIs(self.instance.parent._present(), None)

  def test_007_set_not_present(self):
    self.instance.parent.child._set_present()
    self.assertIs(self.instance.parent.child._present(), True)
    self.instance.parent.child._set_present(present=False)
    self.assertIs(self.instance.parent.child._present(), False)

  def test_008_presence_get(self):
    self.instance.parent.child._set_present()
    self.assertIs(self.instance.empty_container._present(), False)
    self.assertIs(self.instance.parent.child._present(), True)
    self.assertIs(self.instance.pp._present(), False)
    self.assertEqual(self.instance.get(filter=True), {'parent': {'child': {}}})

  def test_009_presence_serialise(self):
    self.instance.parent.child._set_present()
    expectedJ = """
                {
                    "parent": {
                        "child": {}
                    }
                }"""
    self.assertEqual(json.loads(pbJ.dumps(self.instance)), json.loads(expectedJ))

  def test_010_presence_deserialise(self):
    inputJ = """
              {
                "parent": {
                  "child": {}
                }
              }"""
    x = pbJ.loads(inputJ, bindings, "presence")
    self.assertIs(x.parent.child._present(), True)

  def test_011_presence_deserialise(self):
    inputJ = """
              {
                "presence:parent": {
                  "child": {}
                }
              }"""
    x = pbJ.loads_ietf(inputJ, bindings, "presence")
    self.assertIs(x.parent.child._present(), True)


if __name__ == '__main__':
  setup_test()
  args = sys.argv
  if '-k' in args:
    args.remove('-k')
  T = unittest.main(exit=False, argv=args)
  if len(T.result.errors) or len(T.result.failures):
    exitcode = 127
  else:
    exitcode = 0
  teardown_test()
  sys.exit(exitcode)
