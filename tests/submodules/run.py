#!/usr/bin/env python

import os
import sys
import getopt
import unittest
import importlib
from pyangbind.lib.yangtypes import safe_name
import pyangbind.lib.pybindJSON as pbJ
import json

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
  cmd += " %s/mod-a.yang" % (this_dir)
  os.system(cmd)

def teardown_test():
  global k
  global this_dir

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

class PyangbindSubmoduleTests(unittest.TestCase):

  def __init__(self, *args, **kwargs):
    unittest.TestCase.__init__(self, *args, **kwargs)

    err = None
    try:
      globals()["bindings"] = importlib.import_module("bindings")
    except ImportError as e:
      err = e
    self.assertIs(err, None)
    self.instance = bindings.mod_a()

  def test_001_check_correct_import(self):
    self.assertIs(hasattr(self.instance, "a"), True)
    self.assertIs(hasattr(self.instance.a, "b"), True)

  def test_002_identity_in_submodule(self):
    self.assertIs(hasattr(self.instance, "q"), True)
    self.assertIs(hasattr(self.instance.q, "idref"), True)

    passed = True
    try:
      self.instance.q.idref = "j"
    except ValueError:
      passed = False

    self.assertIs(passed, True)

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
